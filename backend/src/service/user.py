import os
from datetime import datetime, timedelta, timezone

from fastapi import BackgroundTasks, HTTPException

from src.core.logger import get_logger
from src.core import security
from src.core.authenticator import (
    create_access_token as create_legacy_access_token,
    create_refresh_token as create_legacy_refresh_token,
)
from src.templates.email import render_email_template, TemplateRenderError
from src.repository.user import (
    SYSTEM_USER_ID,
    add_user,
    get_user_by_email as repo_get_user_by_email,
    get_user_by_pid as repo_get_user_by_pid,
    get_user_by_id as repo_get_user_by_id,
    get_user_by_google_sub as repo_get_user_by_google_sub,
    mark_user_verified as repo_mark_user_verified,
    update_user_password as repo_update_user_password,
    link_user_google_account as repo_link_user_google_account,
    update_user_name as repo_update_user_name,
    insert_user_audit_entry,
    soft_delete_user as repo_soft_delete_user,
)
from src.repository.token import (
    insert_user_token,
    find_active_token_by_hash_and_type,
    consume_token_by_id,
    clear_active_tokens_for_user_type,
    get_last_token_for_user_type,
)
from src.service.email import send_email_and_log, EmailSendError
from src.service.system_limits import ensure_system_capacity

logger = get_logger("service:user")

RESEND_VERIFY_COOLDOWN_SECONDS = int(os.getenv("RESEND_VERIFY_COOLDOWN_SECONDS", "45"))
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
SOCIAL_LINK_TOKEN_TTL_MINUTES = int(os.getenv("SOCIAL_LINK_TOKEN_TTL_MINUTES", "10"))
SUPPORT_URL = f"{FRONTEND_BASE_URL}/support"


def _now_utc() -> datetime:
    # Always return an aware UTC datetime
    return datetime.now(timezone.utc)


def _to_aware_utc(dt: datetime | None) -> datetime | None:
    """Return dt as an aware UTC datetime (treat naive as UTC)."""
    if dt is None:
        return None
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        # If your DB stores naive UTC, this is correct. Adjust if you actually store local time.
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _normalize_name(name: str) -> str:
    cleaned = (name or "").strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="Name is required.")
    if len(cleaned) > 180:
        return cleaned[:180]
    return cleaned


# ------------------------- User creation -------------------------
async def create_user(name: str, email: str, password: str, *, utm_attribution: dict | None = None):
    ensure_system_capacity("user_registrations", 1)
    logger.debug("Hashing password...")
    hashed_password = security.hash_password(password)
    logger.debug("Inserting user into database...")
    return add_user(name, email, hashed_password, utm_attribution=utm_attribution)


async def create_user_with_google(name: str, email: str, google_sub: str):
    """
    Create a passwordless user for Google SSO flows while keeping a hashed secret in the DB.
    """
    logger.debug("Creating user via Google SSO...")
    ensure_system_capacity("user_registrations", 1)
    random_secret = security.generate_raw_token(32)
    hashed_password = security.hash_password(random_secret)
    return add_user(name, email, hashed_password, is_verified=True, google_sub=google_sub)


def get_user_by_email(email: str) -> dict:
    logger.debug("Querying for user with email: %s", email)
    return repo_get_user_by_email(email)


def get_user_by_pid(public_id: str) -> dict:
    logger.debug("Querying for user with public ID: %s", public_id)
    return repo_get_user_by_pid(public_id)


def get_user_by_id(user_id: str) -> dict | None:
    logger.debug("Querying for user with ID: %s", user_id)
    return repo_get_user_by_id(user_id)


def get_user_by_google_sub(google_sub: str) -> dict | None:
    logger.debug("Querying for user with Google sub: %s", google_sub)
    return repo_get_user_by_google_sub(google_sub)


async def send_verification_email(background_tasks: BackgroundTasks, email: str, token: str):
    logger.debug(f"Fetching user with mail {email} from database...")
    user = repo_get_user_by_email(email)
    if not user:
        logger.info("send_verification_email: user not found for email=%s", email)
        raise HTTPException(status_code=404, detail="User not found")

    logger.debug("Queueing verification email to %s", email)
    url = f"{FRONTEND_BASE_URL}/verify-email?token={token}"
    logger.debug(url)
    features = [
        "Secure local-network access",
        "Account recovery for your home assistant",
        "A private workspace for Jarvis",
    ]
    try:
        body = render_email_template(
            "verification",
            {
                "preheader": "Verify your email to activate your Jarvis account.",
                "user_name": user.get("name"),
                "cta_url": url,
                "cta_label": "Verify email",
                "subheadline": "please confirm your email to activate your account.",
                "features": features,
                "footer_note": "If you didn't create a Jarvis account, you can safely ignore this email.",
                "support_url": SUPPORT_URL,
            },
            fallback_plain=f"Verify your email to activate Jarvis: {url}",
        )
    except TemplateRenderError as exc:
        logger.error("Failed to render verification email template: %s", exc)
        raise HTTPException(status_code=503, detail="We could not prepare the verification email.")

    try:
        await send_email_and_log(
            subject="Verify Your Email",
            recipients=[email],
            body=body,
            raise_on_failure=True,
        )
    except EmailSendError as exc:
        logger.error("send_verification_email failed for %s: %s", email, exc)
        raise HTTPException(status_code=503, detail="We could not send the verification email. Please try again later.")


async def send_welcome_email(
    background_tasks: BackgroundTasks | None,
    user: dict,
    *,
    plan_key: str | None = None,
    plan_path: str | None = None,
) -> None:
    """
    Send the welcome email once a user successfully verifies for the first time.
    """
    email = user.get("email")
    if not email:
        return

    name = user.get("name")
    primary_cta_url = f"{FRONTEND_BASE_URL}/account"
    secondary_cta_url = f"{FRONTEND_BASE_URL}/support"
    secondary_cta_label = "Get support"

    features = [
        "Manage your local Jarvis account",
        "Keep access secured behind verified identity",
        "No external account setup required",
    ]

    try:
        body = render_email_template(
            "welcome",
            {
                "preheader": "Your Jarvis account is ready.",
                "user_name": name,
                "cta_url": primary_cta_url,
                "cta_label": "Open Jarvis",
                "secondary_cta_url": secondary_cta_url,
                "secondary_cta_label": secondary_cta_label,
                "plan_label": "Local Access",
                "features": features,
                "support_url": SUPPORT_URL,
            },
            fallback_plain="Welcome to Jarvis! Your account is ready: "
            f"{primary_cta_url}",
        )
    except TemplateRenderError as exc:
        logger.error("Failed to render welcome email template: %s", exc)
        return

    if background_tasks:
        background_tasks.add_task(send_email_and_log, "Welcome to Jarvis", [email], body, "html", False, "personal")
        return

    await send_email_and_log(
        subject="Welcome to Jarvis",
        recipients=[email],
        body=body,
        raise_on_failure=False,
        sender="personal",
    )


def _serialize_user_profile(user: dict) -> dict:
    return {
        "id": str(user.get("id")),
        "public_id": str(user.get("public_id")),
        "email": user.get("email"),
        "name": user.get("name"),
        "is_verified": bool(user.get("is_verified")),
        "created_at": _to_aware_utc(user.get("created_at")),
        "tier_label": "Local",
        "tier_key": "local",
    }


def get_user_profile(user_id: str) -> dict:
    user = repo_get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return _serialize_user_profile(user)


def update_user_profile_name(user_id: str, new_name: str) -> dict:
    user = repo_get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    normalized = _normalize_name(new_name)
    if normalized == (user.get("name") or "").strip():
        return _serialize_user_profile(user)

    updated = repo_update_user_name(user_id, normalized, user_id)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found.")

    try:
        insert_user_audit_entry(
            entity_id=user_id,
            property_name="name",
            original_value=user.get("name"),
            updated_value=normalized,
            acting_user_id=user_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to record user audit for name change: %s", exc)

    return get_user_profile(user_id)


# --------------------- Email verification flow -------------------
async def clear_active_email_tokens_for_user(user_id: int) -> None:
    return clear_active_tokens_for_user_type(user_id, security.TOKEN_TYPE_EMAIL_VERIFICATION)


async def issue_email_verification(email: str, context: dict | None = None) -> str:
    """
    Used during registration (allowed to 404).
    Creates a new single-use token; stores only its SHA-256 hash; returns RAW token.
    """
    user = repo_get_user_by_email(email)
    if not user:
        logger.info("issue_email_verification: user not found for email=%s", email)
        raise HTTPException(status_code=404, detail="User not found")

    user_id = user["id"]
    # Optional policy: enforce only one active token
    try:
        clear_active_tokens_for_user_type(user_id, security.TOKEN_TYPE_EMAIL_VERIFICATION)
    except Exception:
        pass

    raw = security.generate_raw_token(48)
    token_hash = security.hash_token(raw)
    expires_at = _now_utc() + timedelta(hours=security.EMAIL_VERIFICATION_TTL_HOURS)

    insert_user_token(
        user_id=user_id,
        typ=security.TOKEN_TYPE_EMAIL_VERIFICATION,
        token_hash=token_hash,
        expires_at=expires_at,
        context=context or {},
    )
    logger.info("Email verification token issued user_id=%s exp=%s", user_id, expires_at)
    return raw


async def resend_email_verification(
    email: str,
    background_tasks: BackgroundTasks,
    context: dict | None = None,
) -> None:
    """
    Enumeration-safe resend:
    - Always returns None (router will reply { ok: true })
    - If user exists and NOT verified -> respects cooldown -> issues/sends token.
    """
    user = repo_get_user_by_email(email)
    if not user:
        logger.info("resend_email_verification: email not found (generic ok)")
        return

    if user.get("is_verified"):
        logger.info("resend_email_verification: user already verified (generic ok)")
        return

    # Cooldown
    last = None
    try:
        last = get_last_token_for_user_type(user["id"], security.TOKEN_TYPE_EMAIL_VERIFICATION)
    except Exception:
        pass

    if last:
        created_at = last.get("created_at")
        created_at_utc = _to_aware_utc(created_at) if isinstance(created_at, datetime) else None
        if created_at_utc:
            elapsed = (_now_utc() - created_at_utc).total_seconds()
            if elapsed < RESEND_VERIFY_COOLDOWN_SECONDS:
                logger.info("resend_email_verification: cooldown active user_id=%s", user["id"])
                return

    # Reuse the last context if the caller didn't provide one
    if context is None and last:
        context = last.get("context") or {}

    # Issue new token and send email
    raw = await issue_email_verification(email, context=context)
    await send_verification_email(background_tasks, email, raw)
    logger.info("resend_email_verification: email queued for %s", email)


async def verify_email_token(raw_token: str, background_tasks: BackgroundTasks | None = None) -> dict:
    token_hash = security.hash_token(raw_token)
    rec = find_active_token_by_hash_and_type(security.TOKEN_TYPE_EMAIL_VERIFICATION, token_hash)
    if not rec:
        logger.info("verify_email_token: token not found")
        return {"ok": False}

    expires_at = _to_aware_utc(rec["expires_at"])
    if expires_at is None or expires_at <= _now_utc():
        logger.info("verify_email_token: token expired id=%s", rec["id"])
        return {"ok": False}

    user = repo_get_user_by_id(rec["user_id"])
    was_verified = bool(user.get("is_verified")) if user else False
    consume_token_by_id(rec["id"])
    repo_mark_user_verified(rec["user_id"])

    logger.info("verify_email_token: user verified user_id=%s", rec["user_id"])
    plan_key = (rec.get("context") or {}).get("plan_key")
    plan_path = (rec.get("context") or {}).get("plan_path")
    next_path = (rec.get("context") or {}).get("next")

    if not was_verified and user:
        try:
            await send_welcome_email(background_tasks, user, plan_key=plan_key, plan_path=plan_path)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to send welcome email to %s: %s", user.get("email"), exc)

    return {
        "ok": True,
        "user_id": str(rec["user_id"]),
        "email": user.get("email") if user else None,
        "first_verification": not was_verified,
        "plan_key": plan_key,
        "plan_path": plan_path,
        "next": next_path,
    }


async def issue_social_link_token(user_id: str, context: dict) -> str:
    """
    Store Google profile context so the user can explicitly confirm account linking.
    """
    clear_active_tokens_for_user_type(user_id, security.TOKEN_TYPE_SOCIAL_LINK)
    raw = security.generate_raw_token(48)
    token_hash = security.hash_token(raw)
    expires_at = _now_utc() + timedelta(minutes=SOCIAL_LINK_TOKEN_TTL_MINUTES)

    insert_user_token(
        user_id=user_id,
        typ=security.TOKEN_TYPE_SOCIAL_LINK,
        token_hash=token_hash,
        expires_at=expires_at,
        context=context or {},
    )
    logger.info("Social link token issued user_id=%s exp=%s", user_id, expires_at)
    return raw


async def consume_social_link_token(raw_token: str) -> dict:
    token_hash = security.hash_token(raw_token)
    rec = find_active_token_by_hash_and_type(security.TOKEN_TYPE_SOCIAL_LINK, token_hash)
    if not rec:
        logger.info("consume_social_link_token: token not found")
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    expires_at = _to_aware_utc(rec["expires_at"])
    if expires_at is None or expires_at <= _now_utc():
        logger.info("consume_social_link_token: token expired id=%s", rec["id"])
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    consume_token_by_id(rec["id"])
    return rec


def link_user_google_account(user_id: str, google_sub: str) -> None:
    repo_link_user_google_account(user_id, google_sub)
    repo_mark_user_verified(user_id)


# ---------------------- Password reset flow ----------------------
async def issue_password_reset(email: str) -> str | None:
    user = repo_get_user_by_email(email)
    if not user:
        logger.info("issue_password_reset: unknown email (generic ok)")
        return None

    user_id = user["id"]
    try:
        clear_active_tokens_for_user_type(user_id, security.TOKEN_TYPE_PASSWORD_RESET)
    except Exception:
        pass

    raw = security.generate_raw_token(48)
    token_hash = security.hash_token(raw)
    expires_at = _now_utc() + timedelta(hours=security.PASSWORD_RESET_TTL_HOURS)

    insert_user_token(
        user_id=user_id,
        typ=security.TOKEN_TYPE_PASSWORD_RESET,
        token_hash=token_hash,
        expires_at=expires_at,
        context={},
    )
    logger.info("Password reset token issued user_id=%s exp=%s", user_id, expires_at)

    return raw


async def send_password_reset_email(background_tasks: BackgroundTasks | None, email: str) -> None:
    raw_token = await issue_password_reset(email)
    if not raw_token:
        return
    url = f"{FRONTEND_BASE_URL}/reset-password?token={raw_token}"
    user = get_user_by_email(email)
    user_name = user.get("name") if user else None
    try:
        body = render_email_template(
            "reset_password",
            {
                "preheader": "Create a new password to get back into Jarvis.",
                "user_name": user_name,
                "cta_url": url,
                "cta_label": "Reset password",
                "subheadline": "use this secure link to set a fresh password and continue using Jarvis.",
                "support_url": SUPPORT_URL,
                "security_notes": [
                    "Link expires after a short time for security.",
                    "If you didn’t request this, you can ignore this email.",
                    "Never share this link with anyone.",
                ],
            },
            fallback_plain=f"Reset your Jarvis password: {url}",
        )
    except TemplateRenderError as exc:
        logger.error("Failed to render reset password email template: %s", exc)
        raise HTTPException(status_code=503, detail="We could not prepare the reset email.")

    send_kwargs = {
        "subject": "Reset Your Jarvis Password",
        "recipients": [email],
        "body": body,
        "raise_on_failure": True,
    }
    try:
        if background_tasks:
            # Defer send so auth responses stay snappy
            background_tasks.add_task(send_email_and_log, **send_kwargs)
        else:
            await send_email_and_log(**send_kwargs)
    except EmailSendError as exc:
        logger.error("send_password_reset_email failed for %s: %s", email, exc)
        raise HTTPException(status_code=503, detail="We could not send the reset email. Please try again later.")


async def send_password_reset_for_user(background_tasks: BackgroundTasks, user_id: str) -> None:
    user = repo_get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    email = user.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="User is missing an email address.")
    await send_password_reset_email(background_tasks, email)


async def reset_password_using_token(raw_token: str, new_password: str) -> None:
    token_hash = security.hash_token(raw_token)
    rec = find_active_token_by_hash_and_type(security.TOKEN_TYPE_PASSWORD_RESET, token_hash)
    if not rec:
        logger.info("reset_password: token not found")
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    if _to_aware_utc(rec["expires_at"]) <= _now_utc():
        logger.info("reset_password: token expired id=%s", rec["id"])
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    # optional transaction wrapper for atomicity:
    # with_user_transaction():
    consume_token_by_id(rec["id"])
    new_hash = security.hash_password(new_password)
    repo_update_user_password(rec["user_id"], new_hash)
    logger.info("reset_password: password updated user_id=%s", rec["user_id"])


async def change_password_for_authenticated_user(user_id: str, current_password: str, new_password: str) -> None:
    user = repo_get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    hashed = user.get("password") or ""
    if not security.verify_password(current_password, hashed):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")

    new_hash = security.hash_password(new_password)
    repo_update_user_password(user_id, new_hash)
    logger.info("change_password: password updated user_id=%s", user_id)


# --------------------- Account deletion flow ---------------------
async def issue_account_deletion_token(user_id: str) -> str:
    user = repo_get_user_by_id(user_id)
    if not user or user.get("deleted"):
        raise HTTPException(status_code=404, detail="User not found.")

    clear_active_tokens_for_user_type(user_id, security.TOKEN_TYPE_ACCOUNT_DELETION)

    raw = security.generate_raw_token(48)
    token_hash = security.hash_token(raw)
    expires_at = _now_utc() + timedelta(hours=security.ACCOUNT_DELETION_TTL_HOURS)

    insert_user_token(
        user_id=user_id,
        typ=security.TOKEN_TYPE_ACCOUNT_DELETION,
        token_hash=token_hash,
        expires_at=expires_at,
        context={},
    )
    logger.info("Account deletion token issued user_id=%s exp=%s", user_id, expires_at)
    return raw


async def send_account_deletion_email(background_tasks: BackgroundTasks | None, user: dict, raw_token: str) -> None:
    email = user.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="User does not have an email address.")

    url = f"{FRONTEND_BASE_URL}/account/delete?token={raw_token}"
    try:
        body = render_email_template(
            "account_deletion",
            {
                "preheader": "Confirm to permanently delete your Jarvis account.",
                "user_name": user.get("name"),
                "cta_url": url,
                "cta_label": "Delete my account",
                "support_url": SUPPORT_URL,
                "expiry_hours": security.ACCOUNT_DELETION_TTL_HOURS,
            },
            fallback_plain=f"Confirm your Jarvis account deletion: {url}",
        )
    except TemplateRenderError as exc:
        logger.error("Failed to render account deletion email template: %s", exc)
        raise HTTPException(status_code=503, detail="We could not prepare the deletion email.")

    send_kwargs = {
        "subject": "Confirm Your Jarvis Account Deletion",
        "recipients": [email],
        "body": body,
        "raise_on_failure": True,
    }

    try:
        if background_tasks:
            background_tasks.add_task(send_email_and_log, **send_kwargs)
        else:
            await send_email_and_log(**send_kwargs)
    except EmailSendError as exc:
        logger.error("send_account_deletion_email failed for %s: %s", email, exc)
        raise HTTPException(status_code=503, detail="We could not send the deletion email. Please try again later.")


async def request_account_deletion(user_id: str, background_tasks: BackgroundTasks | None) -> None:
    user = repo_get_user_by_id(user_id)
    if not user or user.get("deleted"):
        raise HTTPException(status_code=404, detail="User not found.")

    raw_token = await issue_account_deletion_token(user_id)
    await send_account_deletion_email(background_tasks, user, raw_token)


async def confirm_account_deletion(raw_token: str) -> dict:
    token_hash = security.hash_token(raw_token)
    rec = find_active_token_by_hash_and_type(security.TOKEN_TYPE_ACCOUNT_DELETION, token_hash)
    if not rec:
        logger.info("confirm_account_deletion: token not found")
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    expires_at = _to_aware_utc(rec["expires_at"])
    if expires_at is None or expires_at <= _now_utc():
        logger.info("confirm_account_deletion: token expired id=%s", rec["id"])
        consume_token_by_id(rec["id"])
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user_id = rec["user_id"]
    consume_token_by_id(rec["id"])
    user = repo_get_user_by_id(user_id)

    deleted = repo_soft_delete_user(user_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found.")

    logger.info("confirm_account_deletion: user deleted user_id=%s", user_id)
    return {"ok": True, "email": user.get("email") if user else None}


# --------------------- Login flow ---------------------
async def issue_access_token(user: dict) -> dict:
    token, expires_at = create_legacy_access_token(user)
    return {"token": token, "expires_at": expires_at.isoformat()}


async def issue_refresh_token(user: dict) -> dict:
    token, expires_at = create_legacy_refresh_token(user)
    return {"token": token, "expires_at": expires_at.isoformat()}

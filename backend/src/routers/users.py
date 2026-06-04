import sentry_sdk
import src.model.router as models

from fastapi import APIRouter, HTTPException, Response, BackgroundTasks, Depends, Request
from src.core.logger import get_logger
from src.core.authenticator import get_current_user, verify_refresh_token
from src.core.session_cookie import set_refresh_cookie, clear_refresh_cookie, REFRESH_COOKIE_NAME
from src.core.security import verify_password
from src.repository.blocked_email_domain import is_domain_blocked, log_blocked_registration_attempt
from src.service.user import (
    create_user,
    get_user_by_email,
    get_user_by_pid,
    send_verification_email,
    resend_email_verification,
    issue_email_verification,
    clear_active_email_tokens_for_user,
    verify_email_token,
    issue_access_token,
    issue_refresh_token,
    send_password_reset_email,
    reset_password_using_token,
    get_user_profile,
    update_user_profile_name,
    request_account_deletion,
    confirm_account_deletion,
    send_password_reset_for_user,
    change_password_for_authenticated_user,
)

logger = get_logger("router:users")
router = APIRouter(prefix="/user")


@router.post("/auth/lookup", response_model=models.LookupResponse)
async def email_exists(request: models.LookupRequest):
    try:
        logger.debug(f"Checking if user exists with email: {request.email}")

        # Verify all required fields are present
        if not request.email:
            raise HTTPException(status_code=400, detail="Missing required fields")

        # Check if user exists
        db_user = get_user_by_email(request.email)
        exists = bool(db_user)
        if exists:
            logger.debug(f"Found existing user with email: {request.email}")
            is_verified = bool(db_user.get("is_verified"))
            status = "verified" if is_verified else "unverified"
            return models.LookupResponse(exists=True, is_verified=is_verified, status=status)

        return models.LookupResponse(exists=False)
    except HTTPException as e:
        raise e
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.error(f"Unexpected error during email exists check: {e}")
        raise HTTPException(status_code=500, detail="Failed to check email exists")


@router.post("/auth/login", response_model=models.LoginResponse)
async def login(response: Response, request: models.LoginRequest):
    try:
        sentry_sdk.add_breadcrumb(
            category="auth",
            message="Login attempt",
            data={"email": request.email, "status": "started"},
        )

        # Normalize & decrypt credentials
        user_email = (request.email or "").strip().lower()

        # Fetch user (deleted users excluded)
        db_user = get_user_by_email(user_email)
        if not db_user:
            logger.info("Login failed: user not found")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Verify password
        if not verify_password(request.password, db_user.get("password")):
            logger.info("Login failed: bad password")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Require verified account (treat NULL/False as not verified)
        if not bool(db_user.get("is_verified")):
            logger.info("Login failed: user not verified")
            # Security through Obscurity: don't let the client know the user is not verified
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Issue access tokens
        access_token = await issue_access_token(db_user)
        refresh_token = await issue_refresh_token(db_user)
        set_refresh_cookie(response, refresh_token["token"], refresh_token["expires_at"])

        return {
            "access_token": access_token["token"],
            "access_token_expires_at": access_token["expires_at"],
            "name": db_user.get("name"),
            "email": db_user.get("email"),
            "public_id": db_user.get("public_id"),
            "tier": "local",
        }

    except HTTPException:
        raise
    except Exception as e:
        sentry_sdk.add_breadcrumb(
            category="auth",
            message="Login failed",
            level="error",
            data={"email": request.email, "error": str(e)},
        )
        sentry_sdk.capture_exception(e)
        logger.exception("Error during login")
        raise HTTPException(status_code=500, detail="Failed to log in")


@router.post("/auth/refresh", response_model=models.LoginResponse)
async def refresh_tokens(http_request: Request, response: Response, request: models.RefreshRequest | None = None):
    try:
        refresh_token_value = (request.refresh_token if request else None) or http_request.cookies.get(REFRESH_COOKIE_NAME)
        if not refresh_token_value:
            logger.info(
                "Refresh denied: no token in request body/cookie. origin=%s referer=%s host=%s",
                http_request.headers.get("origin"),
                http_request.headers.get("referer"),
                http_request.headers.get("host"),
            )
            clear_refresh_cookie(response)
            raise HTTPException(status_code=401, detail="Missing refresh token.")

        user = verify_refresh_token(refresh_token_value, consume=True)
        access_token = await issue_access_token(user)
        refresh_token = await issue_refresh_token(user)
        set_refresh_cookie(response, refresh_token["token"], refresh_token["expires_at"])
        logger.debug("Refresh succeeded for user=%s", user.get("id"))
        return {
            "access_token": access_token["token"],
            "access_token_expires_at": access_token["expires_at"],
            "name": user.get("name"),
            "email": user.get("email"),
            "public_id": user.get("public_id"),
            "tier": "local",
        }
    except HTTPException:
        logger.info("Refresh failed with HTTPException")
        clear_refresh_cookie(response)
        raise
    except Exception as exc:
        clear_refresh_cookie(response)
        logger.exception("Error refreshing tokens: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to refresh tokens")

@router.post("/auth/register")
async def register(request: models.RegisterRequest, background_tasks: BackgroundTasks, http_request: Request):
    try:
        logger.debug("Registering new user with data: name=%s, email=%s", request.name, request.email)

        # 1) Basic validation
        if not request.email or not request.name or not request.password:
            raise HTTPException(status_code=400, detail="Missing required fields")

        # 2) Blocked email domain check (security through obscurity: return 503)
        email_domain = str(request.email).split("@", 1)[-1].lower()
        if is_domain_blocked(email_domain):
            ip_header = http_request.headers.get("x-forwarded-for") or http_request.headers.get("X-Real-IP")
            ip_address = ip_header.split(",")[0].strip() if ip_header else (http_request.client.host if http_request.client else None)
            user_agent = http_request.headers.get("user-agent")
            background_tasks.add_task(
                log_blocked_registration_attempt,
                email_domain=email_domain,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            logger.warning("Blocked registration attempt from domain=%r ip=%s", email_domain, ip_address)
            raise HTTPException(status_code=503, detail="Service temporarily unavailable.")

        # 3) Uniqueness check
        existing = get_user_by_email(request.email)
        if existing:
            logger.warning("Attempted to register with existing email: %s", request.email)
            raise HTTPException(status_code=400, detail="Already exists.")

        # 4) Create user (hashing happens in service)
        user = await create_user(request.name, request.email, request.password, utm_attribution=request.utm)

        # 5) Clear existing email tokens for user
        logger.debug("Clearing existing email verification tokens for user with ID: %s", user.get("id"))
        await clear_active_email_tokens_for_user(user.get("id"))

        # 5) Issue verification token via the *service* (stores hash in DB)
        verification_context = {
            "plan_key": request.plan_key,
            "plan_path": request.plan_path,
            "next": request.next,
        }
        raw_token = await issue_email_verification(request.email, context=verification_context)

        # 6) Send verification email (DO NOT log the raw token)
        await send_verification_email(background_tasks, request.email, raw_token)

        logger.info("Registration successful; verification email queued for %s", request.email)
        return {"message": "Successfully registered"}
    except HTTPException:
        raise
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception("Unexpected error during registration")
        raise HTTPException(status_code=500, detail="Failed to register")




# @router.post("/refresh", response_model=models.Token)
# def refresh_token(refresh_data: models.RefreshTokenData = Body(...)):


@router.post("/auth/logout")
async def logout(response: Response):
    clear_refresh_cookie(response)
    return {"ok": True}


@router.post("/auth/send-verification")
async def send_verification(req: models.SendVerificationRequest, bg: BackgroundTasks):
    await resend_email_verification(req.email, bg)
    return {"ok": True}


@router.post("/auth/magic-link")
async def send_magic_link(req: models.MagicLinkRequest, bg: BackgroundTasks):
    """
    Sends a password reset link to the provided email (magic link for sign-in without password).
    Always returns ok to avoid email enumeration.
    """
    await send_password_reset_email(bg, req.email)
    return {"ok": True}


@router.post("/auth/reset-password")
async def reset_password(req: models.ResetPasswordRequest):
    """
    Resets a user's password using a one-time token from their email.
    """
    await reset_password_using_token(req.token, req.new_password)
    return {"ok": True}


@router.post("/auth/confirm-email", response_model=models.ConfirmEmailResponse)
async def confirm_email(req: models.ConfirmEmailRequest, background_tasks: BackgroundTasks):
    result = await verify_email_token(req.token, background_tasks)
    if isinstance(result, dict):
        return result
    return {"ok": bool(result)}


@router.get("/me", response_model=models.AccountProfileResponse)
async def current_user_profile(current_user: dict = Depends(get_current_user)):
    return get_user_profile(str(current_user["id"]))


@router.patch("/profile", response_model=models.AccountProfileResponse)
async def update_profile(request: models.UpdateProfileRequest, current_user: dict = Depends(get_current_user)):
    return update_user_profile_name(str(current_user["id"]), request.name)


@router.post("/auth/send-password-reset")
async def send_authenticated_reset(background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    await send_password_reset_for_user(background_tasks, str(current_user["id"]))
    return {"ok": True}


@router.post("/auth/change-password")
async def change_password(request: models.ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    await change_password_for_authenticated_user(str(current_user["id"]), request.current_password, request.new_password)
    return {"ok": True}


@router.post("/account/delete-request")
async def delete_account_request(background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    await request_account_deletion(str(current_user["id"]), background_tasks)
    return {"ok": True}


@router.post("/account/confirm-delete")
async def delete_account_confirm(request: models.DeleteAccountRequest):
    return await confirm_account_deletion(request.token)


# @router.post("/password-change")
# async def password_change(


# @router.post("/deleteuser")
# def delete_user(current_user: dict = Depends(get_current_user)):
#     return {"message": "Delete user endpoint not implemented"}

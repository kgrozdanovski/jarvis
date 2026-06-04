import asyncio
import os
from functools import partial
from typing import Any, Dict

from fastapi import HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from src.core.logger import get_logger
from src.service.user import (
    get_user_by_email,
    get_user_by_google_sub,
    get_user_by_id,
    create_user_with_google,
    issue_access_token,
    issue_refresh_token,
    issue_social_link_token,
    consume_social_link_token,
    link_user_google_account,
)

logger = get_logger("service:google_auth")

GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID") or os.getenv("GOOGLE_OAUTH_CLIENT_ID")
_google_request = google_requests.Request()


def _ensure_env() -> None:
    if not GOOGLE_OAUTH_CLIENT_ID:
        logger.error("Google OAuth client ID is missing.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google sign-in is not configured.",
        )


async def _verify_id_token(id_token_str: str) -> Dict[str, Any]:
    loop = asyncio.get_running_loop()
    verifier = partial(id_token.verify_oauth2_token, id_token_str, _google_request, GOOGLE_OAUTH_CLIENT_ID)
    try:
        return await loop.run_in_executor(None, verifier)
    except ValueError as exc:
        logger.error("Invalid Google ID token: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid Google token.") from exc


async def fetch_google_profile_from_id_token(id_token_str: str) -> Dict[str, Any]:
    _ensure_env()
    profile = await _verify_id_token(id_token_str)
    email = (profile.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Google account is missing an email address.")

    if not profile.get("email_verified", False):
        raise HTTPException(status_code=400, detail="Google email is not verified.")

    profile["email"] = email
    return profile


async def build_login_response(user: dict) -> Dict[str, Any]:
    access_token = await issue_access_token(user)
    refresh_token = await issue_refresh_token(user)
    return {
        "access_token": access_token["token"],
        "access_token_expires_at": access_token["expires_at"],
        "refresh_token": refresh_token["token"],
        "refresh_token_expires_at": refresh_token["expires_at"],
        "name": user.get("name"),
        "email": user.get("email"),
        "public_id": user.get("public_id"),
        "tier": "local",
    }


async def handle_google_login(credential: str) -> Dict[str, Any]:
    profile = await fetch_google_profile_from_id_token(credential)
    google_sub = profile.get("sub")
    if not google_sub:
        raise HTTPException(status_code=400, detail="Google profile missing subject identifier.")

    existing_google_user = get_user_by_google_sub(google_sub)
    if existing_google_user:
        logger.info("User logged in via Google (already linked) user_id=%s", existing_google_user.get("id"))
        login = await build_login_response(existing_google_user)
        return {"status": "linked", "login": login}

    email = profile["email"]
    existing_email_user = get_user_by_email(email)
    if not existing_email_user:
        user = await create_user_with_google(profile.get("name") or profile["email"], email, google_sub)
        logger.info("Created new user via Google SSO user_id=%s", user.get("id"))
        login = await build_login_response(user)
        return {"status": "created", "login": login}

    token = await issue_social_link_token(
        existing_email_user["id"],
        {
            "google_sub": google_sub,
            "email": email,
            "name": profile.get("name"),
            "picture": profile.get("picture"),
        },
    )
    logger.info("Google SSO link confirmation required user_id=%s", existing_email_user.get("id"))
    return {
        "status": "link_required",
        "link_token": token,
        "email": email,
        "existing_name": existing_email_user.get("name"),
        "google_name": profile.get("name"),
    }


async def confirm_google_link(raw_token: str) -> Dict[str, Any]:
    token_record = await consume_social_link_token(raw_token)
    context = token_record.get("context") or {}
    google_sub = context.get("google_sub")
    if not google_sub:
        raise HTTPException(status_code=400, detail="Link token is missing Google information.")

    user = get_user_by_id(token_record["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    link_user_google_account(user["id"], google_sub)
    logger.info("Linked Google account to user_id=%s", user["id"])

    # Refresh the user entity to include new fields like google_sub / is_verified.
    refreshed_user = get_user_by_google_sub(google_sub) or get_user_by_email(user.get("email"))
    if not refreshed_user:
        raise HTTPException(status_code=500, detail="Unable to load linked user.")

    return await build_login_response(refreshed_user)

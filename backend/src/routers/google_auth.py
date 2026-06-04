import sentry_sdk
from fastapi import APIRouter, HTTPException, Response

import src.model.router as models
from src.core.logger import get_logger
from src.core.session_cookie import set_refresh_cookie
from src.service.google_auth import handle_google_login, confirm_google_link

logger = get_logger("router:google_auth")
router = APIRouter(prefix="/auth/google", tags=["auth"])


@router.post("/login", response_model=models.GoogleAuthExchangeResponse)
async def google_login(request: models.GoogleAuthLoginRequest, response: Response):
    try:
        payload = await handle_google_login(request.credential)
        login_payload = payload.get("login") if isinstance(payload, dict) else None
        if isinstance(login_payload, dict) and login_payload.get("refresh_token"):
            set_refresh_cookie(response, login_payload["refresh_token"], login_payload["refresh_token_expires_at"])
            login_payload.pop("refresh_token", None)
            login_payload.pop("refresh_token_expires_at", None)
        return payload
    except HTTPException:
        raise
    except Exception as exc:
        sentry_sdk.capture_exception(exc)
        logger.exception("Unexpected error during Google exchange: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to sign in with Google.")


@router.post("/link", response_model=models.LoginResponse)
async def google_link(request: models.GoogleLinkConfirmRequest, response: Response):
    try:
        payload = await confirm_google_link(request.token)
        if payload.get("refresh_token"):
            set_refresh_cookie(response, payload["refresh_token"], payload["refresh_token_expires_at"])
            payload.pop("refresh_token", None)
            payload.pop("refresh_token_expires_at", None)
        return payload
    except HTTPException:
        raise
    except Exception as exc:
        sentry_sdk.capture_exception(exc)
        logger.exception("Unexpected error during Google account linking: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to link Google account.")

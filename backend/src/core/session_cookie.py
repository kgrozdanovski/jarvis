import os
from datetime import datetime, timezone

from fastapi import Response


REFRESH_COOKIE_NAME = os.getenv("REFRESH_COOKIE_NAME", "jarvis_refresh")
REFRESH_COOKIE_PATH = os.getenv("REFRESH_COOKIE_PATH", "/user/auth")
REFRESH_COOKIE_DOMAIN = (os.getenv("REFRESH_COOKIE_DOMAIN") or "").strip() or None
REFRESH_COOKIE_SAMESITE = (os.getenv("REFRESH_COOKIE_SAMESITE", "lax") or "lax").strip().lower()


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _secure_cookie_enabled() -> bool:
    override = os.getenv("REFRESH_COOKIE_SECURE")
    if override is not None:
        return _truthy(override)
    app_env = (os.getenv("APP_ENV") or "").strip().lower()
    return app_env in {"prod", "production", "stage"}


def set_refresh_cookie(response: Response, token: str, expires_at: datetime | str) -> None:
    expiry: datetime
    if isinstance(expires_at, str):
        text = expires_at.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        expiry = datetime.fromisoformat(text)
    elif isinstance(expires_at, datetime):
        expiry = expires_at
    else:
        raise ValueError("expires_at must be a datetime or ISO-8601 string")

    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    else:
        expiry = expiry.astimezone(timezone.utc)

    max_age = max(0, int((expiry - datetime.now(timezone.utc)).total_seconds()))
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=max_age,
        expires=expiry,
        path=REFRESH_COOKIE_PATH,
        domain=REFRESH_COOKIE_DOMAIN,
        secure=_secure_cookie_enabled(),
        httponly=True,
        samesite=REFRESH_COOKIE_SAMESITE,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        domain=REFRESH_COOKIE_DOMAIN,
        secure=_secure_cookie_enabled(),
        httponly=True,
        samesite=REFRESH_COOKIE_SAMESITE,
    )

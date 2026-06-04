import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal, Tuple

from fastapi import HTTPException, Request, status

from src.core.crypto import Cryptography
from src.core.dbal import DBAL
from src.core.logger import get_logger

logger = get_logger("core:authenticator")
db = DBAL()
crypto = Cryptography()

ACCESS_TOKEN_KIND: Literal["access"] = "access"
REFRESH_TOKEN_KIND: Literal["refresh"] = "refresh"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "43200"))


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _encode_token_payload(public_id: str, token_base: str) -> str:
    plain_token = f"{public_id}{token_base}"
    encrypted = crypto.encrypt(plain_token)
    return crypto.url_safe_base64_encode(encrypted)


def _persist_token(user_id, token_hash: str, expires_at: datetime) -> None:
    try:
        db.insert(
            "access_token",
            {
                "user_id": user_id,
                "token": token_hash,
                "valid_until": expires_at,
                "created_by": user_id,
                "modified_by": user_id,
            },
        )
    except Exception as exc:  # pragma: no cover - DB errors bubble up
        logger.error("Failed to persist session token: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to persist session token.",
        )


def _create_session_token(user: dict, kind: Literal["access", "refresh"]) -> Tuple[str, datetime]:
    user_id = user.get("id")
    public_id = user.get("public_id")
    if not user_id or not public_id:
        logger.error("Cannot issue token: missing id/public_id on user.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to issue session token.",
        )

    ttl_minutes = (
        ACCESS_TOKEN_EXPIRE_MINUTES if kind == ACCESS_TOKEN_KIND else REFRESH_TOKEN_EXPIRE_MINUTES
    )
    token_base = secrets.token_hex(24)
    encoded = _encode_token_payload(public_id, token_base)
    token_hash = crypto.hash_token(f"{kind}:{token_base}")
    expires_at = _now_utc() + timedelta(minutes=ttl_minutes)
    _persist_token(user_id, token_hash, expires_at)
    return encoded, expires_at


def create_access_token(user: dict) -> Tuple[str, datetime]:
    return _create_session_token(user, ACCESS_TOKEN_KIND)


def create_refresh_token(user: dict) -> Tuple[str, datetime]:
    return _create_session_token(user, REFRESH_TOKEN_KIND)


def _load_user(user_id, expected_public_id: str) -> dict:
    user = db.read_one(
        "users",
        ["id", "public_id", "email", "name", "is_verified"],
        {"id": user_id, "deleted": False},
    )
    if (
        not user
        or user.get("public_id") != expected_public_id
        or not bool(user.get("is_verified"))
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
        )
    return user


def _verify_session_token(
    token_encoded: str,
    kind: Literal["access", "refresh"],
    *,
    consume: bool = False,
) -> dict:
    try:
        encrypted = crypto.url_safe_base64_decode(token_encoded)
        decrypted = crypto.decrypt(encrypted)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
        )

    user_public_id = decrypted[:7]
    token_base = decrypted[7:]
    if len(user_public_id) != 7 or not token_base:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
        )

    token_hash = crypto.hash_token(f"{kind}:{token_base}")
    record = db.read_one(
        "access_token",
        ["id", "user_id", "valid_until"],
        {"token": token_hash, "deleted": False},
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")

    expires_at = _ensure_aware(record.get("valid_until"))
    if expires_at is not None and expires_at <= _now_utc():
        db.delete("access_token", {"id": record["id"]})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired.")

    user = _load_user(record["user_id"], user_public_id)

    if consume:
        db.delete("access_token", {"id": record["id"]})

    return user


def verify_access_token(token_encoded: str) -> dict:
    return _verify_session_token(token_encoded, ACCESS_TOKEN_KIND)


def verify_refresh_token(token_encoded: str, *, consume: bool = True) -> dict:
    return _verify_session_token(token_encoded, REFRESH_TOKEN_KIND, consume=consume)


async def get_current_user(request: Request):
    """
    Dependency to extract and verify the current user based on the Bearer token in the request.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.debug("No token provided in the request headers")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No token provided.")
    token_encoded = auth_header[7:]
    return verify_access_token(token_encoded)



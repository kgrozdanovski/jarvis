import base64
import os
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

from src.core.logger import get_logger
logger = get_logger("core:security")

# -----------------------------------------------------------------------------
# Token types & TTLs for user_tokens table
# -----------------------------------------------------------------------------
TOKEN_TYPE_EMAIL_VERIFICATION = "email_verification"
TOKEN_TYPE_PASSWORD_RESET = "password_reset"
TOKEN_TYPE_SOCIAL_LINK = "social_link"
TOKEN_TYPE_ACCOUNT_DELETION = "account_deletion"

EMAIL_VERIFICATION_TTL_HOURS: int = int(os.getenv("EMAIL_VERIFICATION_TTL_HOURS", "24"))
PASSWORD_RESET_TTL_HOURS: int = int(os.getenv("PASSWORD_RESET_TTL_HOURS", "1"))
ACCOUNT_DELETION_TTL_HOURS: int = int(os.getenv("ACCOUNT_DELETION_TTL_HOURS", "1"))

# -----------------------------------------------------------------------------
# Configuration (env-driven with secure defaults)
# -----------------------------------------------------------------------------
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ISSUER: Optional[str] = os.getenv("JWT_ISSUER") or None
JWT_AUDIENCE: Optional[str] = os.getenv("JWT_AUDIENCE") or None

ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "30"))
VERIFICATION_TOKEN_EXPIRE_HOURS: int = int(os.getenv("VERIFICATION_TOKEN_EXPIRE_HOURS", "24"))

BCRYPT_ROUNDS: int = int(os.getenv("BCRYPT_ROUNDS", "12"))

# AES-256 key (base64 of 32 raw bytes) used by the opaque session-token codec and
# any callers that still use the legacy AES decryption helper below.
_USER_SIGNATURE_PRIVATE_KEY_B64: str = os.getenv("USER_SIGNATURE_PRIVATE_KEY", "")
# Intentionally keeps the requested suffix spelling for deployment compatibility.
_USER_SIGNATURE_PRIVATE_KEY_PREVIUS_B64: str = os.getenv("USER_SIGNATURE_PRIVATE_KEY_PREVIUS", "")

_AES_BLOCK_SIZE_BITS = 128
_AES_BLOCK_SIZE_BYTES = 16


# -----------------------------------------------------------------------------
# URL-safe Base64 with your PHP-compatible mapping (+ -> -, = -> _, / -> ~)
# -----------------------------------------------------------------------------
def url_safe_base64_encode(raw: bytes) -> str:
    logger.debug("Encoding bytes to custom URL-safe Base64 (length=%d)", len(raw))
    b64 = base64.b64encode(raw).decode("ascii")
    return b64.replace("+", "-").replace("=", "_").replace("/", "~")


def url_safe_base64_decode(s: str) -> bytes:
    logger.debug("Decoding custom URL-safe Base64 (length=%d)", len(s))
    restored = s.replace("-", "+").replace("_", "=").replace("~", "/")
    return base64.b64decode(restored)


# -----------------------------------------------------------------------------
# Password hashing & verification (bcrypt)
# -----------------------------------------------------------------------------
def hash_password(plain_password: str) -> str:
    if not isinstance(plain_password, str) or plain_password == "":
        logger.error("hash_password called with empty/invalid password")
        raise ValueError("Password must be a non-empty string.")

    logger.debug("Generating bcrypt salt (rounds=%d)", BCRYPT_ROUNDS)
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    logger.info("Password hashed with bcrypt")
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        logger.debug("verify_password called with missing arguments")
        return False
    try:
        ok = bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        logger.debug("Password verification result: %s", "ok" if ok else "failed")
        return ok
    except Exception as e:
        logger.exception("Error verifying password hash: %s", e)
        return False


def generate_raw_token(length: int = 48) -> str:
    """
    Generate a high-entropy, URL-safe token string.
    48 -> ~288 bits of entropy; safe for verification & reset links.
    """
    if length < 32:
        logger.debug("Token length raised to minimum of 32")
        length = 32
    raw = secrets.token_urlsafe(length)
    logger.debug("Generated raw token (len=%d urlsafe chars)", len(raw))
    return raw


def hash_token(raw: str, as_hex: bool = False):
    """
    Hash a raw token with SHA-256. Return bytes (default for BYTEA) or hex string.
    """
    if not isinstance(raw, str) or not raw:
        logger.error("hash_token called with empty/invalid token")
        raise ValueError("Token must be a non-empty string.")
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    logger.debug("Token hashed with SHA-256")
    return digest.hex() if as_hex else digest


def constant_time_eq(a: bytes, b: bytes) -> bool:
    """
    Constant-time bytes comparison. Prefer hmac.compare_digest.
    """
    try:
        return hmac.compare_digest(a, b)
    except Exception:
        return False


# -----------------------------------------------------------------------------
# AES-256-CBC helpers used by legacy encrypted payload callers.
# -----------------------------------------------------------------------------
def _decode_aes_key(key_b64: str, env_name: str) -> bytes:
    try:
        key = base64.b64decode(key_b64)
    except Exception as e:
        logger.exception("Failed to base64-decode %s: %s", env_name, e)
        raise

    if len(key) != 32:
        logger.error("Invalid AES key length from %s: got %d bytes (expected 32 for AES-256)", env_name, len(key))
        raise RuntimeError(f"{env_name} (decoded) must be exactly 32 bytes.")
    logger.debug("AES key loaded from %s (32 bytes)", env_name)
    return key


def _get_aes_keys_from_env() -> list[tuple[str, bytes]]:
    if not _USER_SIGNATURE_PRIVATE_KEY_B64:
        logger.error("USER_SIGNATURE_PRIVATE_KEY is not set")
        raise RuntimeError("USER_SIGNATURE_PRIVATE_KEY is not set.")

    keys = [("USER_SIGNATURE_PRIVATE_KEY", _decode_aes_key(_USER_SIGNATURE_PRIVATE_KEY_B64, "USER_SIGNATURE_PRIVATE_KEY"))]
    if _USER_SIGNATURE_PRIVATE_KEY_PREVIUS_B64:
        keys.append(
            (
                "USER_SIGNATURE_PRIVATE_KEY_PREVIUS",
                _decode_aes_key(_USER_SIGNATURE_PRIVATE_KEY_PREVIUS_B64, "USER_SIGNATURE_PRIVATE_KEY_PREVIUS"),
            )
        )
    return keys


def _decrypt_aes_cbc(raw: bytes, key: bytes) -> str:
    iv = raw[:_AES_BLOCK_SIZE_BYTES]
    ciphertext = raw[_AES_BLOCK_SIZE_BYTES:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_plain = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(_AES_BLOCK_SIZE_BITS).unpadder()
    plain_bytes = unpadder.update(padded_plain) + unpadder.finalize()
    return plain_bytes.decode("utf-8")


def decrypt_password(encrypted_password: str) -> str:
    """
    Decrypts: urlSafeBase64( IV || AES-256-CBC(plaintext, key, IV) )
    """
    if not isinstance(encrypted_password, str) or encrypted_password == "":
        logger.error("decrypt_password called with empty/invalid input")
        raise ValueError("Encrypted password must be a non-empty string.")

    logger.debug("Starting password decryption (payload length=%d)", len(encrypted_password))
    raw = url_safe_base64_decode(encrypted_password)

    if len(raw) <= _AES_BLOCK_SIZE_BYTES:
        logger.error("Encrypted payload too short: %d bytes", len(raw))
        raise ValueError("Encrypted payload too short.")

    last_error: Exception | None = None

    for env_name, key in _get_aes_keys_from_env():
        try:
            plaintext = _decrypt_aes_cbc(raw, key)
            if env_name != "USER_SIGNATURE_PRIVATE_KEY":
                logger.info("Password payload decrypted successfully with fallback key %s", env_name)
            else:
                logger.info("Password payload decrypted successfully")
            return plaintext
        except Exception as e:
            last_error = e
            logger.warning("Failed to decrypt password payload with %s", env_name)

    logger.error("Failed to decrypt password payload: %s", last_error)
    raise ValueError("Invalid encrypted password.") from last_error


# -----------------------------------------------------------------------------
# JWT helpers
# -----------------------------------------------------------------------------
def _require_jwt_secret() -> str:
    if not JWT_SECRET_KEY:
        logger.error("JWT_SECRET_KEY is not set")
        raise RuntimeError("JWT_SECRET_KEY is not set.")
    return JWT_SECRET_KEY


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_jwt_token(payload: Dict[str, Any], expires_delta: timedelta) -> str:
    if not isinstance(payload, dict):
        logger.error("create_jwt_token called with non-dict payload")
        raise ValueError("JWT payload must be a dict.")

    secret = _require_jwt_secret()
    now = _now()
    to_encode = payload.copy()

    to_encode["iat"] = int(now.timestamp())
    to_encode["nbf"] = int(now.timestamp())
    to_encode["exp"] = int((now + expires_delta).timestamp())
    if JWT_ISSUER:
        to_encode["iss"] = JWT_ISSUER
    if JWT_AUDIENCE:
        to_encode["aud"] = JWT_AUDIENCE

    try:
        token = jwt.encode(to_encode, secret, algorithm=JWT_ALGORITHM)
        if isinstance(token, bytes):
            token = token.decode("utf-8")
        logger.info(
            "JWT created (alg=%s, exp=%s, iss=%s, aud=%s, claims=%s)",
            JWT_ALGORITHM,
            to_encode["exp"],
            JWT_ISSUER,
            JWT_AUDIENCE,
            sorted([k for k in to_encode.keys() if k not in {"exp", "nbf", "iat"}]),
        )
        return token
    except Exception as e:
        logger.exception("Failed to create JWT: %s", e)
        raise


def verify_jwt_token(token: str) -> Dict[str, Any]:
    logger.debug("Verifying JWT (alg=%s, iss=%s, aud=%s)", JWT_ALGORITHM, JWT_ISSUER, JWT_AUDIENCE)
    try:
        secret = _require_jwt_secret()
        options = {
            "require": ["exp", "iat", "nbf"],
            "verify_signature": True,
            "verify_exp": True,
            "verify_nbf": True,
            "verify_iat": True,
        }
        kwargs: Dict[str, Any] = {"algorithms": [JWT_ALGORITHM], "options": options}
        if JWT_ISSUER:
            kwargs["issuer"] = JWT_ISSUER
        if JWT_AUDIENCE:
            kwargs["audience"] = JWT_AUDIENCE

        payload = jwt.decode(token, secret, **kwargs)
        logger.info("JWT successfully verified")
        return payload
    except jwt.ExpiredSignatureError as e:
        logger.info("JWT verification failed: expired")
        raise ValueError("Token has expired.") from e
    except jwt.InvalidTokenError as e:
        logger.info("JWT verification failed: invalid token")
        raise ValueError("Invalid token.") from e
    except Exception as e:
        logger.exception("Unexpected error verifying JWT: %s", e)
        raise


# -----------------------------------------------------------------------------
# Email verification helpers (JWT-based, scoped)
# -----------------------------------------------------------------------------
def create_verification_token(email: str) -> str:
    if not email or "@" not in email:
        logger.error("create_verification_token called with invalid email")
        raise ValueError("A valid email is required to create a verification token.")
    token = create_jwt_token({"sub": email, "scope": "email_verification"},
                             timedelta(hours=VERIFICATION_TOKEN_EXPIRE_HOURS))
    logger.info("Email verification token created (exp in %d hours)", VERIFICATION_TOKEN_EXPIRE_HOURS)
    return token


def verify_token(token: str) -> Optional[str]:
    try:
        logger.debug("Verifying email verification token")
        payload = verify_jwt_token(token)
        scope = payload.get("scope", "")
        if not hmac.compare_digest(scope, "email_verification"):
            logger.info("Verification token rejected due to wrong scope")
            return None
        email = payload.get("sub")
        if not email or "@" not in email:
            logger.info("Verification token rejected due to missing/invalid subject")
            return None
        logger.info("Verification token valid")
        return email
    except Exception as e:
        logger.info("Verification token invalid: %s", e)
        return None

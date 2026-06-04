import os
from datetime import datetime, timedelta, timezone
from src.core.dbal import DBAL
from src.core.logger import get_logger
from src.core.security import generate_api_token_for_db

db = DBAL()
logger = get_logger("repository:access_token")

SYSTEM_USER_ID = os.environ.get("SYSTEM_USER_ID", "8d35b4fb-16f1-4d38-b592-580eaec56a99")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: str, *, ttl_minutes: int | None = None) -> dict:
    """
    Create a long-lived opaque API token row in access_token table.
    Returns {'token': <raw_token>, 'id': <uuid>} — caller must show the token ONCE.
    """
    raw = generate_api_token_for_db()
    expires = (_now_utc() + timedelta(minutes=ttl_minutes)) if ttl_minutes else None

    data = {
        "user_id": user_id,
        "token": raw,                 # stored raw to match VARCHAR(56) DDL
        "valid_until": expires,       # may be NULL (no expiry)
        "created_by": SYSTEM_USER_ID,
        "modified_by": SYSTEM_USER_ID,
    }
    token_id = db.insert("access_token", data, returning="id")["id"]
    logger.info("access_token created id=%s user_id=%s", token_id, user_id)
    return {"id": token_id, "token": raw}


def get_valid_access_token(raw: str) -> dict | None:
    """
    Look up a non-deleted, non-expired access token by its raw value.
    """
    sql = """
      SELECT *
      FROM access_token
      WHERE token = %s
        AND deleted IS NOT TRUE
        AND (valid_until IS NULL OR valid_until > NOW())
      LIMIT 1
    """
    return db.fetch_one(sql, (raw,))


def revoke_access_token_by_id(token_id: str) -> None:
    db.update("access_token", {"deleted": True, "modified_by": SYSTEM_USER_ID}, {"id": token_id})

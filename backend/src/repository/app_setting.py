from __future__ import annotations

from typing import Optional

from src.core.dbal import DBAL
from src.core.logger import get_logger

db = DBAL()
logger = get_logger("repository:app-setting")


def get_setting(key: str) -> Optional[str]:
    row = db.fetch_one(
        "SELECT value FROM app_setting WHERE key = %s LIMIT 1",
        (key,),
    )
    if not row:
        return None
    return row.get("value")


def set_setting(key: str, value: str, acting_user_id: Optional[str]) -> None:
    db.execute(
        """
        INSERT INTO app_setting (key, value, updated_by, updated_at)
        VALUES (%s, %s, %s, NOW())
        ON CONFLICT (key)
        DO UPDATE SET
            value = EXCLUDED.value,
            updated_by = EXCLUDED.updated_by,
            updated_at = NOW()
        """,
        (key, value, acting_user_id),
    )

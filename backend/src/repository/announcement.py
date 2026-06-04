from typing import Optional

from src.core.dbal import DBAL
from src.core.logger import get_logger

db = DBAL()
logger = get_logger("repository:announcement")


def get_active_announcement() -> Optional[dict]:
    """
    Return the most recent announcement within its active window.
    """
    result = db.fetch_one(
        """
        SELECT
            id,
            version,
            message,
            start_at,
            end_at
        FROM system_announcement
        WHERE start_at <= NOW()
          AND (end_at IS NULL OR end_at > NOW())
        ORDER BY start_at DESC
        LIMIT 1
        """
    )
    return result

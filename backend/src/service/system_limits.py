import os
from dataclasses import dataclass
from typing import Dict, Literal, Optional

from fastapi import HTTPException, status

from src.core.dbal import DBAL
from src.core.logger import get_logger

logger = get_logger("service:system-limits")
db = DBAL()

LimitKind = Literal["user_registrations"]


def _env_int(name: str, default: Optional[int] = None) -> Optional[int]:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        logger.warning("Invalid integer for %s=%s; ignoring.", name, raw)
        return default
    return value if value > 0 else default


@dataclass(frozen=True)
class LimitDefinition:
    key: str
    kind: LimitKind
    unit: str
    daily: Optional[int] = None
    monthly: Optional[int] = None

    def enabled(self) -> bool:
        return any(limit is not None for limit in (self.daily, self.monthly))


LIMITS: Dict[str, LimitDefinition] = {
    "user_registrations": LimitDefinition(
        key="user_registrations",
        kind="user_registrations",
        unit="registration(s)",
        daily=_env_int("SYSTEM_LIMIT_USER_REG_DAILY"),
        monthly=_env_int("SYSTEM_LIMIT_USER_REG_MONTHLY"),
    ),
}


def _fetch_user_registration_totals() -> Dict[str, int]:
    row = db.fetch_one(
        """
        SELECT
            COALESCE(COUNT(*) FILTER (WHERE created_at >= date_trunc('day', NOW())), 0) AS daily_count,
            COALESCE(COUNT(*) FILTER (WHERE created_at >= date_trunc('month', NOW())), 0) AS monthly_count
        FROM users
        """
    )
    return {
        "daily": int(row["daily_count"]) if row and "daily_count" in row else 0,
        "monthly": int(row["monthly_count"]) if row and "monthly_count" in row else 0,
    }


def ensure_system_capacity(limit_key: str, amount: int = 1) -> None:
    """
    Guard against exceeding configured global quotas. Raises HTTPException when over limit.
    """
    if amount <= 0:
        return
    definition = LIMITS.get(limit_key)
    if not definition or not definition.enabled():
        return

    totals = _fetch_user_registration_totals()

    if definition.daily is not None and totals["daily"] + amount > definition.daily:
        logger.warning("Daily limit reached for %s", limit_key)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Daily {definition.unit} limit reached. Please try again tomorrow.",
        )

    if definition.monthly is not None and totals["monthly"] + amount > definition.monthly:
        logger.warning("Monthly limit reached for %s", limit_key)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Monthly {definition.unit} limit reached. Please try again next cycle.",
        )

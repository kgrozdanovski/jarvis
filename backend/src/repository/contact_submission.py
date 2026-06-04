from __future__ import annotations

from src.core.dbal import DBAL
from src.core.logger import get_logger

logger = get_logger("repository:contact-submission")
db = DBAL()


def insert_contact_submission(
    *,
    name: str,
    email: str,
    message: str,
    mobile: str | None = None,
    page_url: str | None = None,
    user_id: str | None = None,
    user_plan: str | None = None,
    plan_key: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    try:
        db.insert(
            "contact_submissions",
            {
                "name": name,
                "email": email,
                "message": message,
                "mobile": mobile,
                "page_url": page_url,
                "user_id": user_id,
                "user_plan": user_plan,
                "plan_key": plan_key,
                "ip_address": ip_address,
                "user_agent": user_agent,
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to insert contact submission: %s", exc)
        raise

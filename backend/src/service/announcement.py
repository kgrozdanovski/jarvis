import os
from typing import Optional

from src.core.logger import get_logger
from src.repository.announcement import get_active_announcement as repo_get_active_announcement
from src.service.email import send_email

logger = get_logger("service:announcement")

MAIL_USERNAME = os.getenv("MAIL_USERNAME", "").strip()

_last_notified_version: Optional[str] = None


def get_active_announcement():
    announcement = repo_get_active_announcement()
    if not announcement:
        return None
    return {
        "version": announcement.get("version"),
        "message": announcement.get("message"),
        "start_at": announcement.get("start_at"),
        "end_at": announcement.get("end_at"),
    }


def initialize_announcement_alert() -> None:
    """
    Log and notify admins once per process when an announcement is active.
    """
    global _last_notified_version
    announcement = get_active_announcement()
    if not announcement:
        return
    version = announcement.get("version")
    if not version or version == _last_notified_version:
        return
    logger.critical("System announcement %s: %s", version, announcement.get("message"))
    if MAIL_USERNAME:
        send_email(
            subject=f"System announcement {version}",
            recipients=[MAIL_USERNAME],
            body=f"<p>{announcement.get('message')}</p>",
        )
    _last_notified_version = version

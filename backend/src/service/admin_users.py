from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

from fastapi import BackgroundTasks, HTTPException, status

from src.core.logger import get_logger
from src.repository import admin_user as admin_repo
from src.repository.user import (
    get_user_by_id,
    get_user_by_pid,
    restore_user,
    soft_delete_user,
    user_has_role,
)
from src.service.user import (
    issue_email_verification,
    send_password_reset_email,
    send_verification_email,
)

logger = get_logger("service:admin-users")
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "").strip().lower()


def _resolve_user_record(user_identifier: str) -> Dict[str, object]:
    normalized_identifier = (user_identifier or "").strip()
    if not normalized_identifier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    by_public_id = get_user_by_pid(normalized_identifier)
    if by_public_id:
        return by_public_id

    by_internal_id = get_user_by_id(normalized_identifier)
    if by_internal_id:
        return by_internal_id

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")


def require_admin(user: dict) -> None:
    if not user or not user.get("id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    user_id = str(user["id"])
    if user_has_role(user_id, "admin"):
        return
    email = (user.get("email") or "").strip().lower()
    if MAIL_USERNAME and email == MAIL_USERNAME:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")


def list_users(
    search: Optional[str],
    sort: str,
    limit: int,
    offset: int,
) -> Tuple[List[Dict[str, object]], int]:
    normalized_search = search.strip() if search else None
    rows, total = admin_repo.list_admin_users(
        normalized_search if normalized_search else None,
        sort,
        limit,
        offset,
    )
    users: List[Dict[str, object]] = []
    for row in rows:
        users.append(
            {
                "id": str(row["id"]),
                "public_id": row.get("public_id"),
                "name": row.get("name"),
                "email": row.get("email"),
                "is_verified": bool(row.get("is_verified")),
                "deleted": bool(row.get("deleted")),
                "created_at": row.get("created_at"),
                "last_login_at": row.get("last_login_at"),
            }
        )
    return users, total


def summarize_users() -> Dict[str, int]:
    return admin_repo.get_admin_user_summary()


def perform_soft_delete(user_id: str, acting_user_id: str) -> None:
    user = _resolve_user_record(user_id)
    resolved_user_id = str(user["id"])
    updated = soft_delete_user(resolved_user_id, acting_user_id)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    logger.info("User %s soft-deleted by %s", resolved_user_id, acting_user_id)


def reactivate_user(user_id: str, acting_user_id: str) -> None:
    user = _resolve_user_record(user_id)
    resolved_user_id = str(user["id"])
    restored = restore_user(resolved_user_id, acting_user_id)
    if not restored:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or already active.")
    logger.info("User %s reactivated by %s", resolved_user_id, acting_user_id)


async def resend_verification(user_id: str, background_tasks: BackgroundTasks) -> None:
    user = _resolve_user_record(user_id)
    resolved_user_id = str(user["id"])
    email = user.get("email")
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is missing an email address.")
    token = await issue_email_verification(str(email))
    await send_verification_email(background_tasks, str(email), token)
    logger.info("Verification email reissued for user %s", resolved_user_id)


async def trigger_password_reset(user_id: str, background_tasks: BackgroundTasks) -> None:
    user = _resolve_user_record(user_id)
    resolved_user_id = str(user["id"])
    email = user.get("email")
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is missing an email address.")
    await send_password_reset_email(background_tasks, str(email))
    logger.info("Password reset email queued for user %s", resolved_user_id)

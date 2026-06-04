from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends

import src.model.router as models
from src.core.authenticator import get_current_user
from src.service import admin_users as admin_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=models.AdminUserListResponse)
async def list_admin_users(
    search: str | None = None,
    sort: str = "recent",
    limit: int = 25,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
):
    admin_service.require_admin(current_user)
    safe_limit = max(1, min(limit, 100))
    safe_offset = max(0, offset)
    users, total = admin_service.list_users(search, sort, safe_limit, safe_offset)
    summary = admin_service.summarize_users()
    return {
        "users": users,
        "summary": summary,
        "pagination": {"total": total, "limit": safe_limit, "offset": safe_offset},
    }


@router.post("/users/{user_id}/soft-delete")
async def soft_delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    admin_service.require_admin(current_user)
    admin_service.perform_soft_delete(user_id, str(current_user["id"]))
    return {"ok": True}


@router.post("/users/{user_id}/reactivate")
async def reactivate_user(user_id: str, current_user: dict = Depends(get_current_user)):
    admin_service.require_admin(current_user)
    admin_service.reactivate_user(user_id, str(current_user["id"]))
    return {"ok": True}


@router.post("/users/{user_id}/send-verification")
async def send_verification(
    user_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    admin_service.require_admin(current_user)
    await admin_service.resend_verification(user_id, background_tasks)
    return {"ok": True}


@router.post("/users/{user_id}/reset-password")
async def reset_password(
    user_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    admin_service.require_admin(current_user)
    await admin_service.trigger_password_reset(user_id, background_tasks)
    return {"ok": True}

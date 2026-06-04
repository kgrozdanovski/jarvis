from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import BackgroundTasks, HTTPException

from src.core import security
from src.core.logger import get_logger
from src.repository.newsletter_subscription import (
    get_subscription_by_email,
    get_subscription_by_token_hash,
    mark_unsubscribed,
    upsert_subscription,
)
from src.service.email import queue_email
from src.templates.email import TemplateRenderError, render_email_template

logger = get_logger("service:newsletter")

FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
NEWSLETTER_UNSUBSCRIBE_BASE_URL = (
    os.getenv("NEWSLETTER_UNSUBSCRIBE_BASE_URL")
    or os.getenv("HTTP_API_URL")
    or FRONTEND_BASE_URL
)
NEWSLETTER_CTA_URL = os.getenv("NEWSLETTER_CTA_URL") or FRONTEND_BASE_URL


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _build_unsubscribe_url(raw_token: str) -> str:
    base = NEWSLETTER_UNSUBSCRIBE_BASE_URL.rstrip("/")
    return f"{base}/newsletter/unsubscribe?token={raw_token}"


def _safe_name(name: str | None, email: str) -> str | None:
    if name:
        return name
    try:
        return email.split("@", 1)[0]
    except Exception:
        return None


async def subscribe_to_newsletter(
    background_tasks: BackgroundTasks,
    *,
    email: str,
    name: str | None,
    source: str | None,
    page_url: str | None,
    user_id: str | None,
    user_plan: str | None,
    ip_address: str | None,
    user_agent: str | None,
) -> dict:
    existing = get_subscription_by_email(email)
    rotate_token = existing is None or existing.get("unsubscribed_at") is not None
    raw_unsub_token = security.generate_raw_token(24)
    unsub_hash_hex = security.hash_token(raw_unsub_token, as_hex=True)

    confirmed_at = existing.get("confirmed_at") if existing else None
    record = upsert_subscription(
        email=email,
        name=name,
        source=source,
        page_url=page_url,
        user_id=user_id,
        user_plan=user_plan,
        ip_address=ip_address,
        user_agent=user_agent,
        confirmed_at=confirmed_at or _now_utc(),
        unsubscribe_token_hash=unsub_hash_hex,
        replace_token=rotate_token,
    )

    message = "You are already subscribed."
    if rotate_token and existing is None:
        message = "Thanks for subscribing! Check your inbox for the next issue."
    elif rotate_token:
        message = "Welcome back! You’re resubscribed."
    if rotate_token:
        await _queue_welcome_email(
            background_tasks,
            email=email,
            name=name,
            unsubscribe_token=raw_unsub_token,
            source=source,
        )

    return {
        "subscription": record,
        "message": message,
        "sent_welcome": rotate_token,
    }


async def unsubscribe_from_newsletter(token: str, *, reason: str | None = None) -> dict:
    if not token:
        raise HTTPException(status_code=400, detail="Missing unsubscribe token.")

    try:
        token_hash = security.hash_token(token, as_hex=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid unsubscribe token.") from None

    subscription = get_subscription_by_token_hash(token_hash)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found or already removed.")

    if subscription.get("unsubscribed_at"):
        return {"subscription": subscription, "message": "You are already unsubscribed."}

    updated = mark_unsubscribed(subscription["id"], reason)
    return {"subscription": updated or subscription, "message": "You have been unsubscribed."}


async def _queue_welcome_email(
    background_tasks: BackgroundTasks,
    *,
    email: str,
    name: str | None,
    unsubscribe_token: str,
    source: str | None,
) -> None:
    unsubscribe_url = _build_unsubscribe_url(unsubscribe_token)
    try:
        body = render_email_template(
            "newsletter_welcome",
            {
                "preheader": "You are subscribed to Jarvis updates.",
                "user_name": _safe_name(name, email) or "there",
                "cta_url": NEWSLETTER_CTA_URL,
                "cta_label": "Open Jarvis",
                "unsubscribe_url": unsubscribe_url,
                "source": source or "newsletter",
                "highlights": [
                    "Local-network assistant updates.",
                    "Account and setup improvements.",
                    "Notes about new home automation features.",
                ],
            },
            fallback_plain=(
                "You are subscribed to Jarvis updates. "
                f"Unsubscribe anytime: {unsubscribe_url}"
            ),
        )
    except TemplateRenderError as exc:
        logger.error("Failed to render newsletter welcome email: %s", exc)
        raise HTTPException(status_code=503, detail="Unable to prepare the welcome email.")

    queue_email(
        background_tasks,
        subject="Welcome to Jarvis updates",
        recipients=[email],
        body=body,
        sender="personal",
    )

import html
import os
import time
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Tuple

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from fastapi.responses import HTMLResponse
import src.model.router as models
from src.core.authenticator import verify_access_token
from src.core.logger import get_logger
from src.repository.contact_submission import insert_contact_submission
from src.service.announcement import get_active_announcement
from src.service.email import queue_email, send_email_and_log
from src.service.newsletter import subscribe_to_newsletter, unsubscribe_from_newsletter

# Initialize the logger
logger = get_logger("router.default")
# Initialize a new router
router = APIRouter()

CONTACT_INBOX = os.getenv("CONTACT_INBOX", "contact@jarvis.local")
SUPPORT_INBOX = os.getenv("SUPPORT_INBOX", "support@jarvis.local")
MAX_IP_SUBMISSIONS = 5
MAX_USER_SUBMISSIONS = 3
MAX_GLOBAL_SUBMISSIONS = 100
RATE_LIMIT_WINDOW = 60 * 60  # 1 hour


class InMemoryRateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self.events = defaultdict(list)
        self.lock = Lock()

    def allow(self, key: str) -> bool:
        now = time.time()
        with self.lock:
            window_start = now - self.window_seconds
            recent_events = [ts for ts in self.events[key] if ts >= window_start]
            self.events[key] = recent_events
            if len(recent_events) >= self.limit:
                return False
            self.events[key].append(now)
            return True


ip_rate_limiter = InMemoryRateLimiter(MAX_IP_SUBMISSIONS, RATE_LIMIT_WINDOW)
user_rate_limiter = InMemoryRateLimiter(MAX_USER_SUBMISSIONS, RATE_LIMIT_WINDOW)
global_rate_limiter = InMemoryRateLimiter(MAX_GLOBAL_SUBMISSIONS, RATE_LIMIT_WINDOW)


@router.get("/healthcheck")
async def healthcheck():
    try:
        return {
            "status": "ok"
        }
    except Exception as e:
        logger.error(f"Error occurred in healthcheck: {e}")
        return {
            "message": "Error occurred in healthcheck",
            "error": str(e)
        }


@router.get("/system/announcement")
async def system_announcement():
    return {"announcement": get_active_announcement()}


def _extract_client_meta(request: Request) -> Tuple[str | None, str | None]:
    ip_header = request.headers.get("x-forwarded-for") or request.headers.get("X-Real-IP")
    ip_address = ip_header.split(",")[0].strip() if ip_header else None
    if not ip_address and request.client:
        ip_address = request.client.host
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


def _sanitize_text(value: str | None, max_length: int | None = None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if max_length is not None:
        cleaned = cleaned[:max_length]
    return cleaned if cleaned else None


def _enforce_rate_limits(ip_address: str | None, user_id: str | None) -> None:
    if not global_rate_limiter.allow("global"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many submissions right now. Please try again in a bit.",
        )

    if ip_address and not ip_rate_limiter.allow(ip_address):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many submissions from this IP. Please try again later.",
        )

    if user_id and not user_rate_limiter.allow(user_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many submissions for this account. Please try again later.",
        )


def _resolve_user_context(request: Request, incoming_user_id: str | None, incoming_user_plan: str | None) -> tuple[str | None, str | None]:
    user_id = incoming_user_id
    user_plan = incoming_user_plan
    auth_header = request.headers.get("Authorization")

    if not user_id and auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            user = verify_access_token(token)
            user_id = str(user.get("id") or user.get("public_id")) if user else None
            if not user_plan:
                user_plan = "local"
        except Exception as exc:  # noqa: BLE001
            logger.debug("Optional auth resolution failed for contact submission: %s", exc)

    return user_id, user_plan


def _build_email_payload(
    *,
    name: str,
    email: str,
    message: str,
    topic: str | None,
    company: str | None,
    mobile: str | None,
    plan_key: str | None,
    page_url: str | None,
    user_id: str | None,
    user_plan: str | None,
    ip_address: str | None,
    user_agent: str | None,
) -> tuple[str, str]:
    safe = lambda value: html.escape(value) if value else "N/A"
    escaped_message = html.escape(message).replace("\n", "<br/>")
    submitted_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    subject_parts = ["[Jarvis Contact Form]"]
    if topic:
        subject_parts.append(f"{topic}")
    subject_parts.append(f"New inquiry from {name or 'Unknown'}")
    subject = " ".join(subject_parts)

    body = (
        "You have a new contact form submission.<br/><br/>"
        f"<strong>Name:</strong> {safe(name)}<br/>"
        f"<strong>Email:</strong> {safe(email)}<br/>"
        f"<strong>Company:</strong> {safe(company)}<br/>"
        f"<strong>Mobile:</strong> {safe(mobile)}<br/>"
        f"<strong>Topic:</strong> {safe(topic)}<br/>"
        f"<strong>Plan:</strong> {safe(user_plan or plan_key)}<br/>"
        f"<strong>Page URL:</strong> {safe(page_url)}<br/>"
        f"<strong>User ID:</strong> {safe(user_id)}<br/>"
        f"<br/><strong>Message:</strong><br/>{escaped_message}<br/><br/>"
        f"<strong>IP:</strong> {safe(ip_address)}<br/>"
        f"<strong>User Agent:</strong> {safe(user_agent)}<br/>"
        f"<strong>Submitted:</strong> {safe(submitted_at)}"
    )
    return subject, body


async def _process_contact_submission(
    payload: models.ContactRequest,
    request: Request,
    bg: BackgroundTasks,
    *,
    source: str,
    subject_override: str | None = None,
    recipients_override: list[str] | None = None,
    success_message: str | None = None,
    send_immediately: bool = False,
):
    if payload.honeypot:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid submission.")

    ip_address, user_agent = _extract_client_meta(request)
    user_id, user_plan = _resolve_user_context(request, payload.user_id, payload.user_plan)
    _enforce_rate_limits(ip_address, user_id)

    name = _sanitize_text(payload.name, 100) or ""
    company = _sanitize_text(payload.company, 150)
    topic = _sanitize_text(payload.topic, 50)
    plan_key = _sanitize_text(payload.plan_key or source, 50)
    message = _sanitize_text(payload.message, 3000) or ""
    page_url = str(payload.page_url) if payload.page_url else None
    mobile = _sanitize_text(payload.mobile, 50)

    insert_contact_submission(
        name=name or "Anonymous",
        email=payload.email,
        message=message,
        mobile=mobile,
        page_url=page_url,
        user_id=user_id,
        user_plan=user_plan,
        plan_key=plan_key,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    subject, body = _build_email_payload(
        name=name or "Anonymous",
        email=payload.email,
        message=message,
        topic=topic,
        company=company,
        mobile=mobile,
        plan_key=plan_key,
        page_url=page_url,
        user_id=user_id,
        user_plan=user_plan,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    recipients = recipients_override or [CONTACT_INBOX]
    if send_immediately:
        await send_email_and_log(subject=subject_override or subject, recipients=recipients, body=body)
    else:
        queue_email(bg, subject=subject_override or subject, recipients=recipients, body=body)
    return {"success": True, "message": success_message or "Thank you! Our team will get back to you shortly."}


@router.post("/contact")
async def contact_us(payload: models.ContactRequest, request: Request, bg: BackgroundTasks):
    return await _process_contact_submission(payload, request, bg, source="landing")


@router.post("/support/contact")
async def contact_support(payload: models.ContactRequest, request: Request, bg: BackgroundTasks):
    return await _process_contact_submission(payload, request, bg, source="support")


@router.post("/contact/enterprise")
async def contact_enterprise(payload: models.ContactRequest, request: Request, bg: BackgroundTasks):
    return await _process_contact_submission(
        payload,
        request,
        bg,
        source="enterprise",
        subject_override="[Contact Us] Interest in Enterprise Tier",
        recipients_override=[CONTACT_INBOX],
        success_message="Your request has been received. We will get in touch as soon as possible.",
        send_immediately=True,
    )


@router.post("/newsletter/subscribe")
async def newsletter_subscribe(payload: models.NewsletterSubscribeRequest, request: Request, bg: BackgroundTasks):
    if payload.honeypot:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid submission.")

    ip_address, user_agent = _extract_client_meta(request)
    user_id, user_plan = _resolve_user_context(request, payload.user_id, payload.user_plan)
    _enforce_rate_limits(ip_address, user_id)

    name = _sanitize_text(payload.name, 150)
    source = _sanitize_text(payload.source, 50) or "blog"
    page_url = str(payload.page_url) if payload.page_url else None

    result = await subscribe_to_newsletter(
        bg,
        email=payload.email,
        name=name,
        source=source,
        page_url=page_url,
        user_id=user_id,
        user_plan=user_plan,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return {"success": True, "message": result.get("message") or "You are subscribed."}


@router.post("/newsletter/unsubscribe")
async def newsletter_unsubscribe(payload: models.NewsletterUnsubscribeRequest):
    reason = _sanitize_text(payload.reason, 500)
    result = await unsubscribe_from_newsletter(payload.token, reason=reason)
    return {"success": True, "message": result.get("message")}


@router.get("/newsletter/unsubscribe", response_class=HTMLResponse)
async def newsletter_unsubscribe_link(token: str, reason: str | None = None):
    clean_reason = _sanitize_text(reason, 500)
    status_code = status.HTTP_200_OK
    try:
        result = await unsubscribe_from_newsletter(token, reason=clean_reason)
        message = html.escape(result.get("message") or "Status updated.")
    except HTTPException as exc:
        status_code = exc.status_code
        detail = exc.detail if isinstance(exc.detail, str) else "Unable to update your preferences."
        message = html.escape(detail)
    return HTMLResponse(
        f"""
        <html>
          <body style="font-family: Inter, Arial, sans-serif; padding: 32px; color: #0f172a; background-color: #f8fafc;">
            <div style="max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 24px;">
              <h2 style="margin: 0 0 12px 0; font-size: 22px;">Newsletter preferences</h2>
              <p style="margin: 0 0 8px 0; font-size: 15px; color: #334155;">{message}</p>
              <p style="margin: 0; font-size: 14px; color: #475569;">If this was a mistake, you can re-subscribe anytime from our blog.</p>
            </div>
          </body>
        </html>
        """,
        status_code=status_code,
    )

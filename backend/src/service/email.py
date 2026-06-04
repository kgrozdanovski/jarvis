import asyncio
import os
from typing import Any, Literal, Sequence

import sentry_sdk
from fastapi import BackgroundTasks
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema

from src.core.logger import get_logger
from src.repository.email_log import insert_email_log

logger = get_logger("service:email")

Sender = Literal["system", "personal"]

MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_SERVER = os.getenv("MAIL_SERVER")
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_FROM = os.getenv("MAIL_FROM", MAIL_USERNAME)
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "Jarvis")
MAIL_FROM_SYSTEM = os.getenv("MAIL_FROM_SYSTEM", "no-reply@jarvis.local")
MAIL_FROM_NAME_SYSTEM = os.getenv("MAIL_FROM_NAME_SYSTEM", "Jarvis")
MAIL_PROVIDER = os.getenv("MAIL_PROVIDER", "google")


class EmailSendError(Exception):
    """Raised when an outbound email fails to send."""


def _make_config(mail_from: str | None, mail_from_name: str) -> ConnectionConfig:
    return ConnectionConfig(
        MAIL_USERNAME=MAIL_USERNAME,
        MAIL_PASSWORD=MAIL_PASSWORD,
        MAIL_FROM=mail_from,
        MAIL_FROM_NAME=mail_from_name,
        MAIL_PORT=MAIL_PORT,
        MAIL_SERVER=MAIL_SERVER,
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )


_MAIL_CONFIG_PERSONAL = _make_config(MAIL_FROM, MAIL_FROM_NAME)
_MAIL_CONFIG_SYSTEM = _make_config(MAIL_FROM_SYSTEM, MAIL_FROM_NAME_SYSTEM)


def _config_for(sender: Sender) -> ConnectionConfig:
    return _MAIL_CONFIG_SYSTEM if sender == "system" else _MAIL_CONFIG_PERSONAL


def _from_address_for(sender: Sender) -> str | None:
    return MAIL_FROM_SYSTEM if sender == "system" else MAIL_FROM


def _build_message(subject: str, recipients: Sequence[str], body: str, subtype: str = "html") -> MessageSchema:
    return MessageSchema(
        subject=subject,
        recipients=list(recipients),
        body=body,
        subtype=subtype,
    )


def _serialize_response(response: Any) -> Any:
    if response is None:
        return None
    if isinstance(response, (dict, list, str, int, float, bool)):
        return response
    try:
        return str(response)
    except Exception:  # noqa: BLE001
        return "<unserializable response>"


async def _log_email_async(
    subject: str,
    recipients: Sequence[str],
    body: str,
    status: str,
    provider_response: Any,
    error_message: str | None,
    sender: Sender,
) -> None:
    try:
        await asyncio.to_thread(
            insert_email_log,
            subject,
            _from_address_for(sender),
            recipients,
            body,
            status,
            MAIL_PROVIDER,
            provider_response,
            error_message,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to log outbound email '%s': %s", subject, exc)


async def _deliver_email(subject: str, recipients: Sequence[str], body: str, subtype: str, sender: Sender) -> Any:
    message = _build_message(subject, recipients, body, subtype)
    fm = FastMail(_config_for(sender))
    return await fm.send_message(message)


async def _send_and_log(subject: str, recipients: Sequence[str], body: str, subtype: str, sender: Sender) -> tuple[bool, str | None]:
    if not recipients:
        return False, "No recipients provided"
    status = "sent"
    provider_response: Any = None
    error_message: str | None = None
    try:
        provider_response = _serialize_response(await _deliver_email(subject, recipients, body, subtype, sender))
    except Exception as exc:  # noqa: BLE001
        status = "failed"
        error_message = str(exc)
        logger.error("Failed to send email '%s': %s", subject, exc)
        sentry_sdk.capture_exception(exc)
    await _log_email_async(subject, recipients, body, status, provider_response, error_message, sender)

    return status == "sent", error_message


def queue_email(
    background_tasks: BackgroundTasks,
    subject: str,
    recipients: Sequence[str],
    body: str,
    subtype: str = "html",
    sender: Sender = "system",
) -> None:
    """
    Enqueue an email to be sent via FastMail using FastAPI background tasks.
    """
    if not recipients:
        return
    try:
        background_tasks.add_task(_send_and_log, subject, recipients, body, subtype, sender)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to enqueue email '%s': %s", subject, exc)


def send_email(
    subject: str,
    recipients: Sequence[str],
    body: str,
    subtype: str = "html",
    sender: Sender = "system",
) -> None:
    """
    Fire-and-forget helper for synchronous contexts; schedules on an event loop when available.
    """
    if not recipients:
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(_send_and_log(subject, recipients, body, subtype, sender))
    else:
        loop.create_task(_send_and_log(subject, recipients, body, subtype, sender))


async def send_email_and_log(
    subject: str,
    recipients: Sequence[str],
    body: str,
    subtype: str = "html",
    raise_on_failure: bool = False,
    sender: Sender = "system",
) -> bool:
    """
    Send email immediately (not via BackgroundTasks) and log the outcome.
    Useful for flows where the caller needs to know if delivery failed.
    """
    success, error_message = await _send_and_log(subject, recipients, body, subtype, sender)
    if not success and raise_on_failure:
        raise EmailSendError(error_message or "Failed to send email")
    return success

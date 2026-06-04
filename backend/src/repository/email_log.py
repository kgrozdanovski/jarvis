from __future__ import annotations

from typing import Any, Sequence

from psycopg.types.json import Json

from src.core.dbal import DBAL
from src.core.logger import get_logger

logger = get_logger("repository:email-log")
db = DBAL()


def _normalize_response(provider_response: Any) -> Any:
    if provider_response is None:
        return None
    if isinstance(provider_response, (dict, list)):
        return provider_response
    return {"message": str(provider_response)}


def insert_email_log(
    subject: str,
    sender: str | None,
    recipients: Sequence[str],
    body: str | None,
    status: str,
    provider: str,
    provider_response: Any = None,
    error_message: str | None = None,
) -> None:
    try:
        normalized_response = _normalize_response(provider_response)
        db.execute(
            """
            INSERT INTO email_log (subject, sender, recipients, body, status, provider, provider_response, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                subject,
                sender,
                list(recipients),
                body,
                status,
                provider,
                Json(normalized_response) if normalized_response is not None else None,
                error_message,
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to insert email_log row: %s", exc)

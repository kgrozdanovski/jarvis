from __future__ import annotations

from typing import Any, Dict

from fastapi import Request


_TRUNCATE = 512


def _trim(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    return value[:_TRUNCATE]


def extract_client_metadata(request: Request) -> Dict[str, Any]:
    """
    Snapshot of the inbound request used for audit/forensics.

    Captures originating IP (honouring X-Forwarded-For/X-Real-IP), user agent,
    referer, and a few correlation IDs that proxies/CDNs commonly inject.
    Values are trimmed to keep JSONB payload sizes bounded.
    """
    headers = request.headers
    forwarded_for = headers.get("x-forwarded-for") or headers.get("X-Real-IP")
    ip_address = forwarded_for.split(",")[0].strip() if forwarded_for else None
    if not ip_address and request.client:
        ip_address = request.client.host

    metadata: Dict[str, Any] = {
        "ip_address": _trim(ip_address),
        "user_agent": _trim(headers.get("user-agent")),
        "referer": _trim(headers.get("referer")),
        "origin": _trim(headers.get("origin")),
        "forwarded_for": _trim(forwarded_for),
        "request_id": _trim(headers.get("x-request-id")),
        "host": _trim(headers.get("host")),
        "accept_language": _trim(headers.get("accept-language")),
        "method": request.method,
        "path": request.url.path,
    }
    return {k: v for k, v in metadata.items() if v is not None}


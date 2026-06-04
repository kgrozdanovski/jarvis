"""
Background service that tails the nginx access log and inserts anonymized
traffic records into the traffic_log table.

Runs as an asyncio background task started on FastAPI app startup.
"""
from __future__ import annotations

import asyncio
import hashlib
import os
import re
import time
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from src.core.dbal import DBAL
from src.core.logger import get_logger

logger = get_logger("service:traffic-log-ingestion")

ACCESS_LOG_PATH = os.getenv("NGINX_ACCESS_LOG_PATH", "/var/log/nginx/jarvis.access.log")
OFFSET_FILE_PATH = os.getenv("TRAFFIC_LOG_OFFSET_PATH", "/code/storage/traffic_log_offset.txt")
POLL_INTERVAL_SECONDS = 5
BATCH_SIZE = 100
BATCH_FLUSH_INTERVAL_SECONDS = 10

# Regex for the custom nginx log format:
# $ip_truncated - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" "$http_cf_ipcountry"
_LOG_PATTERN = re.compile(
    r'^(?P<ip>\S+)\s+-\s+\S+\s+\[(?P<time>[^\]]+)\]\s+'
    r'"(?P<method>\S+)\s+(?P<path>\S+)\s+\S+"\s+'
    r'(?P<status>\d{3})\s+(?P<bytes>\S+)\s+'
    r'"(?P<referrer>[^"]*)"\s+"(?P<ua>[^"]*)"\s+"(?P<country>[^"]*)"'
)

# Static asset extensions and paths to skip
_STATIC_ASSET_RE = re.compile(
    r'\.(js|css|png|jpg|jpeg|gif|webp|ico|woff|woff2|ttf|svg|otf|mp4)(\?.*)?$',
    re.IGNORECASE,
)
_NUXT_PATH_RE = re.compile(r'^/_nuxt/')

db = DBAL()


def _hash_ip(ip: str) -> str:
    """SHA-256 hash of the (already truncated) IP for unique visitor counting."""
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()


def _extract_referrer_domain(referrer: str) -> Optional[str]:
    """Extract just the domain from the Referer header. Returns None for empty/self."""
    if not referrer or referrer == "-":
        return None
    try:
        parsed = urlparse(referrer)
        domain = parsed.hostname
        if not domain:
            return None
        # Strip www. prefix for cleaner aggregation
        if domain.startswith("www."):
            domain = domain[4:]
        return domain[:512]
    except Exception:
        return None


def _classify_device(user_agent: str) -> str:
    """Classify a user-agent string into a broad device category."""
    if not user_agent or user_agent == "-":
        return "desktop"
    ua_lower = user_agent.lower()
    if any(tok in ua_lower for tok in ("bot", "crawler", "spider", "scrapy", "headless", "wget", "curl")):
        return "bot"
    if any(tok in ua_lower for tok in ("tablet", "ipad")):
        return "tablet"
    if any(tok in ua_lower for tok in ("mobile", "android", "iphone")):
        return "mobile"
    return "desktop"


def _should_skip(path: str, status_code: int) -> bool:
    """Return True if this log line should be excluded from traffic_log."""
    # Only keep 2xx and 3xx responses
    if status_code < 200 or status_code >= 400:
        return True
    # Skip static assets
    if _STATIC_ASSET_RE.search(path):
        return True
    if _NUXT_PATH_RE.match(path):
        return True
    return False


def _parse_line(line: str) -> Optional[dict]:
    """Parse a single nginx access log line into a dict ready for insertion."""
    m = _LOG_PATTERN.match(line.strip())
    if not m:
        return None

    status_code = int(m.group("status"))
    path = m.group("path")

    if _should_skip(path, status_code):
        return None

    bytes_sent = m.group("bytes")
    response_bytes = int(bytes_sent) if bytes_sent.isdigit() else None

    country = m.group("country").strip()
    if not country or country == "-" or len(country) != 2:
        country = None

    return {
        "ip_hash": _hash_ip(m.group("ip")),
        "request_path": path[:2048],
        "http_method": m.group("method")[:10],
        "status_code": status_code,
        "response_bytes": response_bytes,
        "referrer_domain": _extract_referrer_domain(m.group("referrer")),
        "country_code": country,
        "device_category": _classify_device(m.group("ua")),
    }


def _read_offset() -> int:
    """Read the last consumed file offset from disk."""
    try:
        with open(OFFSET_FILE_PATH, "r") as f:
            content = f.read().strip()
            return int(content) if content else 0
    except (FileNotFoundError, ValueError):
        return 0


def _write_offset(offset: int) -> None:
    """Persist the current file offset to disk."""
    try:
        os.makedirs(os.path.dirname(OFFSET_FILE_PATH), exist_ok=True)
        with open(OFFSET_FILE_PATH, "w") as f:
            f.write(str(offset))
    except OSError as exc:
        logger.warning("Failed to write offset file: %s", exc)


def _insert_batch(records: List[dict]) -> None:
    """Batch-insert parsed traffic records into the database."""
    if not records:
        return

    columns = [
        "ip_hash", "request_path", "http_method", "status_code",
        "response_bytes", "referrer_domain", "country_code", "device_category",
    ]
    placeholders = ", ".join(["%s"] * len(columns))
    values_clauses = ", ".join([f"({placeholders})"] * len(records))
    cols_str = ", ".join(columns)

    params: list = []
    for rec in records:
        for col in columns:
            params.append(rec.get(col))

    query = f"INSERT INTO traffic_log ({cols_str}) VALUES {values_clauses}"

    try:
        db.execute(query, tuple(params))
        logger.debug("Inserted %d traffic_log records", len(records))
    except Exception as exc:
        logger.error("Failed to insert traffic_log batch (%d records): %s", len(records), exc)
        raise


def _read_new_lines(path: str, offset: int) -> Tuple[List[str], int]:
    """
    Read new lines from the log file starting at *offset*.
    Handles file rotation (file shrunk or inode changed) by resetting to 0.
    Returns (lines, new_offset).
    """
    try:
        file_size = os.path.getsize(path)
    except OSError:
        return [], offset

    # Detect log rotation: file is smaller than our offset
    if file_size < offset:
        logger.info("Log file appears rotated (size %d < offset %d). Resetting offset.", file_size, offset)
        offset = 0

    if file_size == offset:
        return [], offset

    try:
        with open(path, "r", errors="replace") as fh:
            fh.seek(offset)
            lines = fh.readlines()
            new_offset = fh.tell()
        return lines, new_offset
    except OSError as exc:
        logger.warning("Could not read log file %s: %s", path, exc)
        return [], offset


async def _ingest_loop() -> None:  # noqa: C901
    """
    Main polling loop: read new lines, parse, batch-insert.
    Runs forever until the task is cancelled.
    """
    offset = _read_offset()
    batch: List[dict] = []
    last_flush = time.monotonic()

    logger.info(
        "Traffic log ingestion started. log=%s offset=%d poll=%ds",
        ACCESS_LOG_PATH, offset, POLL_INTERVAL_SECONDS,
    )

    while True:
        try:
            lines, new_offset = _read_new_lines(ACCESS_LOG_PATH, offset)

            for line in lines:
                record = _parse_line(line)
                if record:
                    batch.append(record)

            now = time.monotonic()
            should_flush = (
                len(batch) >= BATCH_SIZE
                or (batch and now - last_flush >= BATCH_FLUSH_INTERVAL_SECONDS)
            )

            if should_flush:
                try:
                    _insert_batch(batch)
                    offset = new_offset
                    _write_offset(offset)
                    batch = []
                    last_flush = now
                except Exception:
                    # On DB error, keep the batch and retry next cycle.
                    # Don't advance the offset so data is not lost.
                    logger.warning("Batch insert failed; will retry on next cycle.")
            else:
                # Even if we didn't flush, advance offset if no records were produced
                # (all lines were filtered out).
                if not batch:
                    offset = new_offset
                    _write_offset(offset)

        except Exception as exc:
            logger.exception("Unexpected error in traffic ingestion loop: %s", exc)

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def start_traffic_log_ingestion() -> None:
    """
    Entry point called from FastAPI startup.
    Spawns the ingestion loop as a background asyncio task.
    """
    asyncio.create_task(_ingest_loop())
    logger.info("Traffic log ingestion task scheduled.")

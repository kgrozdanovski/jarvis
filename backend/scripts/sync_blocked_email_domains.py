#!/usr/bin/env python3
"""
sync_blocked_email_domains.py
------------------------------
Fetches disposable/temporary email domain lists from multiple public sources,
deduplicates them, and syncs the result into the blocked_email_domains table.

Sync semantics
--------------
- Domains present in the new aggregate and NOT in DB → INSERT (active).
- Domains present in the new aggregate and already inactive in DB → reactivate
  (UPDATE is_active=TRUE, clear deleted_at).
- Domains currently active in DB but absent from the new aggregate → soft-delete
  (UPDATE is_active=FALSE, set deleted_at=NOW()).
- All UPDATEs produce audit rows in blocked_email_domains_audit.

Safety guards
-------------
- If a source returns an HTTP error or empty body it is skipped; the others
  still contribute to the aggregate.
- If ALL sources fail, the DB is left untouched — the previous blocklist is
  preserved.
- Bulk operations are batched in chunks of BATCH_SIZE to avoid huge single
  transactions and excessive memory use.

Invocation
----------
Called by the weekly GitHub Actions workflow via:
    python3 scripts/script.py --name sync_blocked_email_domains
"""

from __future__ import annotations

import json
import logging
import re
import sys
import uuid
from datetime import datetime, timezone

import psycopg
import requests

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("sync_blocked_email_domains")

# ---------------------------------------------------------------------------
# Sources
# Each entry: (name, url, format)
# format: "lines" → one domain per line (strip whitespace, skip # comments)
#         "json"  → top-level JSON array of strings
# ---------------------------------------------------------------------------
SOURCES: list[tuple[str, str, str]] = [
    (
        "disposable-email-domains",
        "https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/master/disposable_email_blocklist.conf",
        "lines",
    ),
    (
        "mailchecker",
        "https://raw.githubusercontent.com/FGRibreau/mailchecker/master/list.txt",
        "lines",
    ),
    (
        "burner-email-providers",
        "https://raw.githubusercontent.com/wesbos/burner-email-providers/master/emails.txt",
        "lines",
    ),
    (
        "fakefilter",
        "https://raw.githubusercontent.com/7c/fakefilter/main/txt/data.txt",
        "lines",
    ),
]

# Maximum seconds to wait for a single HTTP response.
HTTP_TIMEOUT = 30

# Rows per INSERT / UPDATE batch.
BATCH_SIZE = 500

# Basic domain sanity check: at least one dot, only safe characters.
_DOMAIN_RE = re.compile(r"^[a-z0-9]([a-z0-9\-\.]*[a-z0-9])?(\.[a-z]{2,})$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_source(name: str, url: str, fmt: str) -> set[str]:
    """Fetch one source and return a set of lower-cased domain strings."""
    logger.info("Fetching source %r …", name)
    try:
        resp = requests.get(url, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Source %r failed (%s) — skipping.", name, exc)
        return set()

    text = resp.text.strip()
    if not text:
        logger.warning("Source %r returned empty body — skipping.", name)
        return set()

    domains: set[str] = set()
    if fmt == "json":
        try:
            items = json.loads(text)
            if not isinstance(items, list):
                logger.warning("Source %r JSON is not a list — skipping.", name)
                return set()
            for item in items:
                if isinstance(item, str):
                    domains.add(item.strip().lower())
        except json.JSONDecodeError as exc:
            logger.warning("Source %r JSON parse error (%s) — skipping.", name, exc)
            return set()
    else:  # "lines"
        for line in text.splitlines():
            line = line.strip().lower()
            if not line:
                continue
            if line.startswith("##"):
                # Section-header format used by fakefilter et al.: "## mailswipe.net"
                # The text after the hashes is the provider domain itself — include it.
                candidate = line.lstrip("#").strip()
                if candidate:
                    domains.add(candidate)
            elif line.startswith("#"):
                # Plain comment — skip entirely.
                continue
            else:
                domains.add(line)

    # Basic validation
    valid = {d for d in domains if _DOMAIN_RE.match(d)}
    dropped = len(domains) - len(valid)
    if dropped:
        logger.debug("Source %r: dropped %d invalid domain strings.", name, dropped)

    logger.info("Source %r: %d valid domains.", name, len(valid))
    return valid


def _chunks(lst: list, size: int):
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


# ---------------------------------------------------------------------------
# DB helpers (raw psycopg — bypasses DBAL to use executemany efficiently)
# ---------------------------------------------------------------------------

def _get_connection():
    """Build a psycopg connection using the same env vars as the DBAL."""
    import os
    from dotenv import load_dotenv

    load_dotenv()
    dsn = (
        f"postgresql://{os.environ['DB_USERNAME']}:{os.environ['DB_PASSWORD']}"
        f"@{os.environ['DB_HOSTNAME']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
    )
    return psycopg.connect(dsn, autocommit=False)


def _load_all_db_domains(cur) -> dict[str, dict]:
    """
    Return a mapping of domain → row dict for every row in blocked_email_domains.
    """
    cur.execute(
        "SELECT id, domain, is_active, sources FROM blocked_email_domains"
    )
    rows = cur.fetchall()
    return {row["domain"]: row for row in rows}


def _insert_new_domains(cur, domains: list[str], source_names: list[str], run_id: uuid.UUID) -> int:
    """Bulk-insert brand-new domains in batches. Returns count inserted."""
    sources_json = json.dumps(source_names)
    inserted = 0
    for batch in _chunks(domains, BATCH_SIZE):
        cur.executemany(
            """
            INSERT INTO blocked_email_domains (domain, is_active, sources)
            VALUES (%s, TRUE, %s::jsonb)
            ON CONFLICT (domain) DO NOTHING
            """,
            [(d, sources_json) for d in batch],
        )
        inserted += cur.rowcount if cur.rowcount >= 0 else len(batch)
    return inserted


def _reactivate_domains(cur, domain_rows: list[dict], new_sources_json: str, run_id: uuid.UUID) -> int:
    """
    Set is_active=TRUE for domains that were soft-deleted but have re-appeared.
    Writes audit rows for each change.
    """
    if not domain_rows:
        return 0

    ids = [r["id"] for r in domain_rows]
    cur.execute(
        """
        UPDATE blocked_email_domains
        SET is_active   = TRUE,
            sources     = %s::jsonb,
            updated_at  = NOW(),
            deleted_at  = NULL
        WHERE id = ANY(%s)
        """,
        (new_sources_json, ids),
    )
    changed = cur.rowcount

    audit_rows = [
        (run_id, r["id"], r["domain"], "is_active", "false", "true", "sync_script")
        for r in domain_rows
    ]
    _write_audit_rows(cur, audit_rows)
    return changed


def _deactivate_domains(cur, domain_rows: list[dict], run_id: uuid.UUID) -> int:
    """
    Soft-delete domains that are no longer present in any source.
    Writes audit rows for each change.
    """
    if not domain_rows:
        return 0

    ids = [r["id"] for r in domain_rows]
    cur.execute(
        """
        UPDATE blocked_email_domains
        SET is_active  = FALSE,
            updated_at = NOW(),
            deleted_at = NOW()
        WHERE id = ANY(%s)
        """,
        (ids,),
    )
    changed = cur.rowcount

    audit_rows = [
        (run_id, r["id"], r["domain"], "is_active", "true", "false", "sync_script")
        for r in domain_rows
    ]
    _write_audit_rows(cur, audit_rows)
    return changed


def _write_audit_rows(cur, rows: list[tuple]) -> None:
    """
    Bulk-insert audit records into blocked_email_domains_audit.
    rows: list of (run_id, entity_id, domain, property_name, old_value, new_value, changed_by)
    """
    if not rows:
        return
    for batch in _chunks(rows, BATCH_SIZE):
        cur.executemany(
            """
            INSERT INTO blocked_email_domains_audit
                (run_id, entity_id, domain, property_name,
                 original_value_string, updated_value_string, changed_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            batch,
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    run_id = uuid.uuid4()
    started_at = datetime.now(timezone.utc)
    logger.info("=== sync_blocked_email_domains start | run_id=%s ===", run_id)

    # 1) Fetch all sources
    aggregate: set[str] = set()
    succeeded_sources: list[str] = []
    for name, url, fmt in SOURCES:
        result = _fetch_source(name, url, fmt)
        if result:
            aggregate.update(result)
            succeeded_sources.append(name)

    if not aggregate:
        logger.critical(
            "All sources failed or returned no data.  Aborting — existing blocklist preserved."
        )
        sys.exit(1)

    logger.info(
        "Aggregate: %d unique domains from %d/%d sources.",
        len(aggregate),
        len(succeeded_sources),
        len(SOURCES),
    )

    # 2) Sync to DB
    conn = _get_connection()
    try:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            db_map = _load_all_db_domains(cur)

            active_db   = {d: r for d, r in db_map.items() if r["is_active"]}
            inactive_db = {d: r for d, r in db_map.items() if not r["is_active"]}

            to_insert     = sorted(aggregate - set(db_map))
            to_reactivate = [inactive_db[d] for d in aggregate if d in inactive_db]
            to_deactivate = [active_db[d]   for d in active_db  if d not in aggregate]

            logger.info(
                "Plan: insert=%d  reactivate=%d  deactivate=%d",
                len(to_insert), len(to_reactivate), len(to_deactivate),
            )

            sources_json = json.dumps(succeeded_sources)

            n_inserted    = _insert_new_domains(cur, to_insert, succeeded_sources, run_id)
            n_reactivated = _reactivate_domains(cur, to_reactivate, sources_json, run_id)
            n_deactivated = _deactivate_domains(cur, to_deactivate, run_id)

        conn.commit()
        elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
        logger.info(
            "=== sync complete in %.1fs | inserted=%d reactivated=%d deactivated=%d ===",
            elapsed, n_inserted, n_reactivated, n_deactivated,
        )
    except Exception:
        conn.rollback()
        logger.exception("Sync failed — transaction rolled back.")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

from __future__ import annotations

from src.core.dbal import DBAL
from src.core.logger import get_logger

logger = get_logger("repository:blocked-email-domain")
db = DBAL()

# Maximum number of log inserts allowed from the same IP within the rate-limit
# window before we start silently dropping duplicates.  Prevents a single
# source from flooding registration_security_log.
_LOG_RATE_LIMIT = 10
_LOG_RATE_LIMIT_WINDOW = "5 minutes"


def is_domain_blocked(domain: str) -> bool:
    """
    Return True if the given domain appears in the active blocklist.

    Uses the partial index idx_blocked_email_domains_active for a single
    index-only scan — safe to call on every registration request.
    """
    try:
        row = db.fetch_one(
            """
            SELECT EXISTS (
                SELECT 1
                FROM blocked_email_domains
                WHERE domain = %s
                  AND is_active = TRUE
            ) AS blocked
            """,
            (domain.lower(),),
        )
        return bool(row and row.get("blocked"))
    except Exception:
        # On any DB error, fail open: do not block the registration.
        logger.exception("Failed to check blocked email domain for %r; failing open", domain)
        return False


def log_blocked_registration_attempt(
    *,
    email_domain: str,
    ip_address: str | None,
    user_agent: str | None,
) -> None:
    """
    Append a row to registration_security_log for a blocked-domain attempt.

    Before inserting, checks how many rows this IP has produced in the last
    _LOG_RATE_LIMIT_WINDOW.  If at or above _LOG_RATE_LIMIT the insert is
    silently skipped — the incident is already on record and we do not want
    a single attacker to fill the table.

    This function is designed to be called from a BackgroundTask so it never
    delays the HTTP response.
    """
    try:
        if ip_address:
            count_row = db.fetch_one(
                f"""
                SELECT COUNT(*) AS cnt
                FROM registration_security_log
                WHERE ip_address = %s::inet
                  AND created_at > NOW() - INTERVAL '{_LOG_RATE_LIMIT_WINDOW}'
                """,
                (ip_address,),
            )
            if count_row and int(count_row.get("cnt", 0)) >= _LOG_RATE_LIMIT:
                logger.debug(
                    "Skipping security log insert for %s — rate limit reached (%d/%d in %s)",
                    ip_address,
                    int(count_row.get("cnt", 0)),
                    _LOG_RATE_LIMIT,
                    _LOG_RATE_LIMIT_WINDOW,
                )
                return

        db.insert(
            "registration_security_log",
            {
                "event_type": "blocked_email_domain",
                "email_domain": email_domain,
                "ip_address": ip_address,
                "user_agent": user_agent,
            },
        )
        logger.info(
            "Blocked registration attempt logged: domain=%r ip=%s",
            email_domain,
            ip_address,
        )
    except Exception:
        # Never raise — this is a background audit write.
        logger.exception(
            "Failed to log blocked registration attempt for domain %r", email_domain
        )

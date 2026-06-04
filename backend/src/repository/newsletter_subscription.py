from __future__ import annotations

from src.core.dbal import DBAL
from src.core.logger import get_logger

db = DBAL()
logger = get_logger("repository:newsletter-subscription")


def get_subscription_by_email(email: str) -> dict | None:
    return db.fetch_one(
        "SELECT * FROM newsletter_subscriptions WHERE lower(email) = lower(%s)",
        (email,),
    )


def get_subscription_by_token_hash(token_hash: str) -> dict | None:
    return db.fetch_one(
        "SELECT * FROM newsletter_subscriptions WHERE unsubscribe_token_hash = %s",
        (token_hash,),
    )


def upsert_subscription(
    *,
    email: str,
    name: str | None,
    source: str | None,
    page_url: str | None,
    user_id: str | None,
    user_plan: str | None,
    ip_address: str | None,
    user_agent: str | None,
    confirmed_at,
    unsubscribe_token_hash: str,
    replace_token: bool,
) -> dict:
    """
    Insert a new newsletter subscription or reactivate/update an existing one.
    When replace_token is True, the unsubscribe token hash will be rotated.
    """
    return db.fetch_one(
        """
        INSERT INTO newsletter_subscriptions (
            email, name, source, page_url, user_id, user_plan,
            ip_address, user_agent, confirmed_at, unsubscribed_at,
            unsubscribe_reason, unsubscribe_token_hash, created_at, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, NULL, %s, now(), now())
        ON CONFLICT (email) DO UPDATE SET
            name = EXCLUDED.name,
            source = EXCLUDED.source,
            page_url = EXCLUDED.page_url,
            user_id = EXCLUDED.user_id,
            user_plan = EXCLUDED.user_plan,
            ip_address = EXCLUDED.ip_address,
            user_agent = EXCLUDED.user_agent,
            updated_at = now(),
            confirmed_at = COALESCE(newsletter_subscriptions.confirmed_at, EXCLUDED.confirmed_at),
            unsubscribed_at = NULL,
            unsubscribe_reason = NULL,
            unsubscribe_token_hash = CASE
                WHEN %s THEN EXCLUDED.unsubscribe_token_hash
                ELSE newsletter_subscriptions.unsubscribe_token_hash
            END
        RETURNING *
        """,
        (
            email,
            name,
            source,
            page_url,
            user_id,
            user_plan,
            ip_address,
            user_agent,
            confirmed_at,
            unsubscribe_token_hash,
            replace_token,
        ),
    )


def mark_unsubscribed(subscription_id: str, reason: str | None = None) -> dict | None:
    return db.fetch_one(
        """
        UPDATE newsletter_subscriptions
        SET unsubscribed_at = now(),
            unsubscribe_reason = %s,
            updated_at = now()
        WHERE id = %s
        RETURNING *
        """,
        (reason, subscription_id),
    )

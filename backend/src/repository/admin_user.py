from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from src.core.dbal import DBAL
from src.core.logger import get_logger

db = DBAL()
logger = get_logger("repository:admin-user")


def list_admin_users(
    search: Optional[str],
    sort: str,
    limit: int,
    offset: int,
) -> Tuple[List[dict], int]:
    filters: List[str] = []
    params: List[object] = []

    if search:
        like = f"%{search.lower()}%"
        filters.append("(LOWER(u.name) LIKE %s OR LOWER(u.email) LIKE %s)")
        params.extend([like, like])

    filter_sql = " AND " + " AND ".join(filters) if filters else ""
    if sort == "name":
        order_clause = "u.deleted ASC, LOWER(u.name) ASC"
    else:
        order_clause = "u.deleted ASC, COALESCE(last_login.last_seen, u.created_at) DESC, u.created_at DESC"

    params.extend([limit, offset])
    rows = db.fetch_all(
        f"""
        SELECT
            u.id,
            u.public_id,
            u.name,
            u.email,
            u.is_verified,
            u.deleted,
            u.created_at,
            last_login.last_seen AS last_login_at,
            COUNT(*) OVER() AS total_count
        FROM users u
        LEFT JOIN LATERAL (
            SELECT MAX(created_at) AS last_seen
            FROM access_token tok
            WHERE tok.user_id = u.id
        ) AS last_login ON TRUE
        WHERE TRUE
        {filter_sql}
        ORDER BY {order_clause}
        LIMIT %s OFFSET %s
        """,
        tuple(params),
    )

    total = int(rows[0]["total_count"]) if rows else 0
    return rows, total


def get_admin_user_summary() -> Dict[str, int]:
    row = db.fetch_one(
        """
        WITH last_seen AS (
            SELECT
                u.id,
                MAX(tok.created_at) AS last_login_at
            FROM users u
            LEFT JOIN access_token tok ON tok.user_id = u.id
            WHERE u.deleted = FALSE
            GROUP BY u.id
        )
        SELECT
            COUNT(*) AS total_users,
            COUNT(*) FILTER (
                WHERE last_login_at IS NOT NULL
                  AND last_login_at >= date_trunc('day', NOW())
            ) AS active_today
        FROM last_seen
        """
    )
    if not row:
        return {"total_users": 0, "active_today": 0}
    return {
        "total_users": int(row.get("total_users") or 0),
        "active_today": int(row.get("active_today") or 0),
    }

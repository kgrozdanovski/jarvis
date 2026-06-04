import os
import random
import uuid
from datetime import datetime, timezone

from src.core.dbal import DBAL
from src.core.logger import get_logger

db = DBAL()
logger = get_logger("repository:user")

SYSTEM_USER_ID = os.environ.get("SYSTEM_USER_ID", "8d35b4fb-16f1-4d38-b592-580eaec56a99")


def add_user(name: str, email: str, password: str, *, is_verified: bool = False, google_sub: str | None = None, utm_attribution: dict | None = None) -> dict:
    public_id = random.randint(1000000, 9999999)

    data = {
        'public_id': public_id,
        'name': name,
        'email': email,
        'password': password,
        'is_verified': is_verified,
        'created_by': SYSTEM_USER_ID,
        'modified_by': SYSTEM_USER_ID
    }
    if google_sub:
        data['google_sub'] = google_sub
    if utm_attribution:
        data['utm_attribution'] = utm_attribution
    result = db.insert('users', data, 'id')
    logger.debug(f"Created user with ID: {result.get('id')}")

    # Read the entity from the database and return it
    user = db.read_one('users', [], {'id': result.get('id')})

    return user


def get_user_by_email(email: str) -> dict:
    return db.read_one('users', [], {'email': email, 'deleted': False})


def get_user_by_pid(public_id: str) -> dict:
    return db.read_one('users', [], {'public_id': public_id, 'deleted': False})


def get_user_by_id(user_id: str) -> dict | None:
    return db.read_one('users', [], {'id': user_id, 'deleted': False})


def get_user_by_google_sub(google_sub: str) -> dict | None:
    return db.read_one('users', [], {'google_sub': google_sub, 'deleted': False})


def mark_user_verified(user_id: str) -> None:
    db.update('users', {'is_verified': True}, {'id': user_id})


def update_user_password(user_id: str, new_hash: str) -> None:
    db.update('users', {'password': new_hash}, {'id': user_id})


def link_user_google_account(user_id: str, google_sub: str) -> None:
    db.update('users', {'google_sub': google_sub}, {'id': user_id})


def user_has_role(user_id: str, role_name: str) -> bool:
    row = db.fetch_one(
        """
        SELECT 1
        FROM user_role ur
        JOIN role r ON r.id = ur.role_id
        WHERE ur.user_id = %s
          AND ur.deleted = FALSE
          AND r.deleted = FALSE
          AND LOWER(r.name) = LOWER(%s)
        LIMIT 1
        """,
        (user_id, role_name),
    )
    return bool(row)


def soft_delete_user(user_id: str, acting_user_id: str) -> bool:
    now = datetime.now(timezone.utc)
    updated = db.update(
        "users",
        {"deleted": True, "modified_by": acting_user_id, "modified_at": now},
        {"id": user_id, "deleted": False},
    )
    return bool(updated)


def restore_user(user_id: str, acting_user_id: str) -> bool:
    now = datetime.now(timezone.utc)
    updated = db.update(
        "users",
        {"deleted": False, "modified_by": acting_user_id, "modified_at": now},
        {"id": user_id, "deleted": True},
    )
    return bool(updated)


def insert_user_audit_entry(
    *,
    entity_id: str,
    property_name: str,
    original_value: str | None,
    updated_value: str | None,
    acting_user_id: str,
) -> None:
    db.insert(
        "user_audit",
        {
            "request_id": str(uuid.uuid4()),
            "entity_id": entity_id,
            "property_name": property_name,
            "original_value_string": original_value,
            "updated_value_string": updated_value,
            "created_by": acting_user_id,
        },
    )


def update_user_name(user_id: str, new_name: str, acting_user_id: str) -> bool:
    now = datetime.now(timezone.utc)
    updated = db.update(
        "users",
        {"name": new_name, "modified_by": acting_user_id, "modified_at": now},
        {"id": user_id, "deleted": False},
    )
    return bool(updated)

import os

from src.core.dbal import DBAL
from src.core.logger import get_logger

db = DBAL()
logger = get_logger("repository:token")

SYSTEM_USER_ID = os.environ.get("SYSTEM_USER_ID", "8d35b4fb-16f1-4d38-b592-580eaec56a99")


def insert_user_token(user_id: str, typ: str, token_hash: bytes, expires_at, context: dict) -> str:
    data = {
        'user_id': user_id,
        'type': typ,
        'token_hash': token_hash,
        'context': context or {},
        'expires_at': expires_at,
        'created_by': SYSTEM_USER_ID,
        'modified_by': SYSTEM_USER_ID,
        'deleted': False
    }
    token_id = db.insert('user_tokens', data)
    logger.debug(f"Created token of type {typ} with ID: {token_id}")

    return token_id


def find_active_token_by_hash_and_type(typ: str, token_hash: bytes) -> dict | None:
    logger.debug("Finding active token of type %s with hash: %s", typ, token_hash.hex())

    return db.fetch_one(
        "SELECT * FROM user_tokens WHERE type = %s AND token_hash = decode(%s, 'hex') AND used_at IS NULL AND deleted = FALSE",
        [typ, token_hash.hex()]
    )


def consume_token_by_id(token_id: str) -> None:
    logger.debug("Consuming token with ID: %s", token_id)
    db.update('user_tokens', {'used_at': db.now()}, {'id': token_id})


def clear_active_tokens_for_user_type(user_id: str, typ: str) -> None:
    logger.debug("Clearing active tokens of type %s for user ID %s", typ, user_id)
    db.update('user_tokens', {'deleted': True}, {'user_id': user_id, 'type': typ})


def get_last_token_for_user_type(user_id: str, typ: str) -> dict | None:
    # todo: implement optional sorting logic in DBAL
    return db.read_one('user_tokens', [], {'user_id': user_id, 'type': typ, 'used_at': None, 'deleted': False})

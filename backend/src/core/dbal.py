import os
import time
from typing import Any, Iterable, Optional, Tuple

import psycopg
from psycopg_pool import ConnectionPool
from psycopg import errors as pg_errors
from psycopg.types.json import Json
import sentry_sdk
from src.core.logger import get_logger
from dotenv import load_dotenv

load_dotenv()

DB_USERNAME = os.environ.get('DB_USERNAME')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_HOSTNAME = os.environ.get('DB_HOSTNAME')
DB_PORT = os.environ.get('DB_PORT')
DB_NAME = os.environ.get('DB_NAME')

DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOSTNAME}:{DB_PORT}/{DB_NAME}"

logger = get_logger("core:dbal")

# One pool per process; every DBAL instance reuses it.
_pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=1,
    max_size=10,
    # kwargs are passed to psycopg.connect for each new conn:
    kwargs={"autocommit": False, "connect_timeout": 5}
)


def _is_sql_null(value: Any) -> bool:
    """Treat Python None or the string 'NULL' (any case/whitespace) as SQL NULL."""
    return value is None or (isinstance(value, str) and value.strip().upper() == "NULL")


def _normalize_value(value: Any) -> Any:
    """Normalize Python values before binding to SQL placeholders."""
    if _is_sql_null(value):
        return None
    if isinstance(value, (dict, list)):
        # Ensure JSONB columns receive properly adapted payloads.
        return Json(value)
    return value


def _safe_params(params: Optional[Iterable], max_len: int = 500) -> Optional[Tuple[Any, ...]]:
    """Truncate long param values for logs/Sentry; keep types visible."""
    if params is None:
        return None
    safe = []
    for p in params:
        if isinstance(p, (bytes, bytearray)):
            safe.append(f"<bytes:{len(p)}>")
        elif isinstance(p, str) and len(p) > max_len:
            safe.append(p[:max_len] + f"...<{len(p)} chars>")
        else:
            safe.append(p)
    return tuple(safe)


def _is_retryable(exc: Exception) -> bool:
    """Conservative set of retryable errors."""
    return isinstance(exc, (
        pg_errors.SerializationFailure,    # 40001
        pg_errors.DeadlockDetected,        # 40P01
        pg_errors.CannotConnectNow,        # 57P03
        pg_errors.AdminShutdown,           # 57P01
        pg_errors.TooManyConnections,      # 53300
        pg_errors.ConnectionDoesNotExist,  # 08003
        pg_errors.ConnectionException,     # 08000 family
    ))


def make_select_query(
        table: str,
        columns: list = None,
        where: dict = None
) -> tuple:
    """
    Create a SELECT query with optional WHERE clause.

    :param table: Name of the table.
    :param columns: List of columns to select; selects all if None.
    :param where: Optional dictionary for WHERE clause conditions.
    """
    columns_str = ', '.join(columns) if columns else '*'
    query = f"SELECT {columns_str} FROM {table}"
    params = ()
    if where:
        clauses = []
        values = []
        for col, val in where.items():
            if _is_sql_null(val):
                # server-side binding doesn’t support `IS %s`; use a literal IS NULL
                clauses.append(f"{col} IS NULL")
            else:
                # normal equality
                clauses.append(f"{col} = %s")
                values.append(val)
        where_clause = ' AND '.join(clauses)
        query += f" WHERE {where_clause}"
        params = tuple(values)

    return query, params


class DBAL:
    def __init__(self):
        # keep a reference to the pool (shared)
        self.pool = _pool

    # ---------- helpers ----------

    def now(self):
        with self.pool.connection() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cursor:
                cursor.execute("SELECT NOW()")
                return cursor.fetchone()["now"]

    def _run(
        self,
        query: str,
        params: Optional[Tuple[Any, ...]] = None,
        *,
        mode: str = "none",  # "none" | "one" | "all"
        retries: int = 2,
        retry_backoff_base: float = 0.1,  # seconds
    ):
        """
        Centralized executor: commit/rollback, logging, Sentry, and optional retries.
        """
        # Shallow, safe versions for logs/Sentry
        safe_params = _safe_params(params)
        attempt = 0
        while True:
            attempt += 1
            with self.pool.connection() as conn:
                try:
                    with conn.cursor(row_factory=psycopg.rows.dict_row) as cursor:
                        logger.debug(f"SQL attempt {attempt}: {query} | Params: {safe_params}")
                        cursor.execute(query, params)
                        if mode == "one":
                            result = cursor.fetchone()
                        elif mode == "all":
                            result = cursor.fetchall()
                        else:
                            result = None
                    conn.commit()
                    return result
                except Exception as exc:
                    try:
                        conn.rollback()
                    except Exception:
                        pass

                    # Add Sentry context + breadcrumb once per attempt
                    sentry_sdk.set_context("sql", {
                        "query": query,
                        "params": safe_params,
                        "attempt": attempt,
                        "mode": mode,
                    })
                    sentry_sdk.capture_exception(exc)

                    logger.error(
                        f"DB error on attempt {attempt}: {exc} | SQL: {query} | Params: {safe_params}"
                    )

                    if attempt <= retries and _is_retryable(exc):
                        # Exponential-ish backoff
                        time.sleep(retry_backoff_base * (2 ** (attempt - 1)))
                        continue
                    raise  # bubble up after retries exhausted

    # ---------- Core operations ----------

    def execute(self, query: str, params: tuple = None) -> None:
        """
        Execute a non-select query (INSERT/UPDATE/DELETE) without returning rows.
        """
        self._run(query, params, mode="none")

    def fetch_all(self, query: str, params: tuple = None) -> list:
        """
        Execute a SELECT query and return all records.

        :param query:
        :param params:
        :return:
        """
        return self._run(query, params, mode="all")

    def fetch_one(self, query: str, params: tuple = None):
        """
        Execute a SELECT query and return a single record.

        :param query:
        :param params:
        :return:
        """
        return self._run(query, params, mode="one")

    def insert(self, table: str, data: dict, returning: str = None):
        """
        Insert a new record into a table.

        :param table: Name of the table.
        :param data: Dictionary where keys are column names and values are the corresponding data.
        :param returning: Optional column to return (e.g., primary key).

        :return: The value of the returning column if specified, otherwise None.
        """
        columns, placeholders, values = [], [], []
        for key, value in data.items():
            columns.append(key)
            if isinstance(value, str) and value.startswith("fn_"):
                placeholders.append(value.replace("fn_", "", 1))
            else:
                placeholders.append("%s")
                values.append(_normalize_value(value))

        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        if returning:
            query += f" RETURNING {returning}"
        params = tuple(values)
        mode = "one" if returning else "none"

        return self._run(query, params, mode=mode)

    def update(self, table: str, data: dict, where: dict) -> int:
        """
        Update records in a table.
        :param table: Name of the table.
        :param data: Dictionary of columns and their new values.
        :param where: Dictionary for the WHERE clause conditions.
        :return: The number of rows updated.
        """
        set_clause = ', '.join([f"{col} = %s" for col in data.keys()])

        where_clauses, where_vals = [], []
        for col, val in where.items():
            if _is_sql_null(val):
                where_clauses.append(f"{col} IS NULL")
            else:
                where_clauses.append(f"{col} = %s")
                where_vals.append(val)

        where_clause = ' AND '.join(where_clauses)
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        params = tuple(_normalize_value(v) for v in data.values()) + tuple(where_vals)

        # _run returns None; we need rowcount, so do it inline once:
        with self.pool.connection() as conn:
            try:
                with conn.cursor(row_factory=psycopg.rows.dict_row) as cursor:
                    logger.debug(f"Executing update: {query} | Params: {_safe_params(params)}")
                    cursor.execute(query, params)
                    affected = cursor.rowcount
                conn.commit()
                return affected
            except Exception as exc:
                try:
                    conn.rollback()
                except Exception:
                    pass
                sentry_sdk.set_context("sql", {
                    "query": query, "params": _safe_params(params), "mode": "none"
                })
                sentry_sdk.capture_exception(exc)
                logger.error(f"Error updating table {table}: {exc}")
                # Optionally retry here using _run pattern; for brevity, re-raise:
                raise

    def delete(self, table: str, where: dict) -> int:
        """
        Delete records from a table.
        :param table: Name of the table.
        :param where: Dictionary for the WHERE clause conditions.
        :return: The number of rows deleted.
        """
        where_clause = ' AND '.join([f"{col} = %s" for col in where.keys()])
        query = f"DELETE FROM {table} WHERE {where_clause}"
        params = tuple(where.values())

        # _run returns None; we need rowcount, so do it inline once:
        with self.pool.connection() as conn:
            try:
                with conn.cursor(row_factory=psycopg.rows.dict_row) as cursor:
                    logger.debug(f"Executing delete: {query} | Params: {_safe_params(params)}")
                    cursor.execute(query, params)
                    affected = cursor.rowcount
                conn.commit()
                return affected
            except Exception as exc:
                try:
                    conn.rollback()
                except Exception:
                    pass
                sentry_sdk.set_context("sql", {
                    "query": query, "params": _safe_params(params), "mode": "none"
                })
                sentry_sdk.capture_exception(exc)
                logger.error(f"Error deleting from table {table}: {exc}")
                raise

    # ---------- convenience ----------

    def read(self, table: str, columns: list = None, where: dict = None):
        """
        Read records from a table.
        :param table: Name of the table.
        :param columns: List of columns to select; selects all if None.
        :param where: Optional dictionary for WHERE clause conditions.

        :return: A single record or a list of records.
        """
        query, params = make_select_query(table, columns, where)

        return self.fetch_all(query, params)

    def read_one(self, table: str, columns: list = None, where: dict = None):
        """
        Read records from a table.
        :param table: Name of the table.
        :param columns: List of columns to select; selects all if None.
        :param where: Optional dictionary for WHERE clause conditions.

        :return: A single record or a list of records.
        """
        if not columns or columns == []:
            columns = ["*"]

        query, params = make_select_query(table, columns, where)

        return self.fetch_one(query, params)

    def transaction(self):
        """
        Pooled transaction context:
            with DBAL().transaction() as cursor:
                cursor.execute("SQL ...")
        Ensures a single leased connection for the whole transaction.
        """
        return PooledTransaction(self.pool)


class PooledTransaction:
    def __init__(self, pool: ConnectionPool):
        self.pool = pool
        self._pool_cm = None
        self.conn = None
        self.cursor = None

    def __enter__(self):
        # Lease one connection for the whole transaction
        self._pool_cm = self.pool.connection()
        self.conn = self._pool_cm.__enter__()
        self.cursor = self.conn.cursor(row_factory=psycopg.rows.dict_row)
        logger.debug("Starting transaction (pooled)")
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                self.conn.rollback()
                logger.error("Transaction rolled back due to exception",
                             exc_info=(exc_type, exc_val, exc_tb))
            else:
                self.conn.commit()
                logger.debug("Transaction committed successfully")
        finally:
            try:
                if self.cursor:
                    self.cursor.close()
            finally:
                # Return connection to the pool
                self._pool_cm.__exit__(exc_type, exc_val, exc_tb)
                self.conn = None
                self.cursor = None
                self._pool_cm = None

import logging
import psycopg2
from psycopg2 import extras
from typing import List, Tuple
from .config import DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT

logger = logging.getLogger(__name__)


def get_db_connection():
    """
    Create and return a new PostgreSQL connection using configuration from `config`.

    Returns:
        A new psycopg2 connection instance.
    """
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT
    )


def execute_batch_insert(insert_sql: str, data: List[Tuple]) -> int:
    """
    Execute a batch INSERT/UPSERT using psycopg2.extras.execute_values.

    Args:
        insert_sql: SQL statement with a single VALUES %s placeholder for execute_values.
        data: List of tuples to insert.

    Returns:
        Number of affected rows (int).
    """
    if not data:
        logger.debug("No data to insert, skipping execute_batch_insert")
        return 0

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        conn.autocommit = False
        cur = conn.cursor()
        extras.execute_values(cur, insert_sql, data)
        conn.commit()
        logger.info(f"Inserted/Updated {cur.rowcount} rows")
        return cur.rowcount

    except Exception:
        logger.exception("Error inserting batch into database")
        if conn:
            conn.rollback()
        raise

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

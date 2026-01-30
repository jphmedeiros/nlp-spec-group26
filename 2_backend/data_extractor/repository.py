import logging
from typing import List, Tuple, Optional
from .db import execute_batch_insert, get_db_connection
import psycopg2.extras

logger = logging.getLogger(__name__)

UPSERT_PROPOSITION_WORD_CLOUD = """
    INSERT INTO proposition_word_cloud (id, word, frequency) 
    VALUES %s
    ON CONFLICT (id, word) DO UPDATE SET frequency = EXCLUDED.frequency
"""

UPSERT_PROPOSITION_SUMMARY = """
    INSERT INTO proposition_summary (id, text_summary, main_theme, sentiment, ideology) 
    VALUES %s
    ON CONFLICT (id) DO UPDATE SET
      text_summary = EXCLUDED.text_summary,
      main_theme = EXCLUDED.main_theme,
      sentiment = EXCLUDED.sentiment,
      ideology = EXCLUDED.ideology
"""

UPSERT_PROPOSITION_NER = """
    INSERT INTO proposition_ner (id, entity_type, entity) 
    VALUES %s
    ON CONFLICT (id, entity_type, entity) DO NOTHING
"""

UPSERT_AUTHORS = """
    INSERT INTO authors (id, full_name, poli_party, uf) 
    VALUES %s
    ON CONFLICT (id) DO UPDATE SET full_name = EXCLUDED.full_name, poli_party = EXCLUDED.poli_party, uf = EXCLUDED.uf
"""

UPSERT_PROPOSITION_TOPICS = """
    INSERT INTO proposition_topics (id, topic)
    VALUES %s
    ON CONFLICT (id) DO UPDATE SET
        topic = EXCLUDED.topic;
"""

UPSERT_PROPOSITIONS = """
    INSERT INTO propositions (id, url_full_text, proposition_type, submission_date, authors) 
    VALUES %s
    ON CONFLICT (id) DO UPDATE SET url_full_text = EXCLUDED.url_full_text, proposition_type = EXCLUDED.proposition_type, submission_date = EXCLUDED.submission_date, authors = EXCLUDED.authors
"""


def insert_word_clouds_batch(data: List[Tuple[int, str, int]]) -> int:
    """
    Insert a batch of word cloud rows.

    Args:
        data: List of tuples (id, word, frequency)

    Returns:
        Number of affected rows.
    """
    logger.debug(f"Inserting word cloud batch of size: {len(data)}")
    return execute_batch_insert(UPSERT_PROPOSITION_WORD_CLOUD, data)


def insert_proposition_summaries_batch(data: List[Tuple[int, str, str, str, str]]) -> int:
    """
    Insert a batch of proposition summaries.

    Args:
        data: List of tuples (id, text_summary, main_theme, sentiment, ideology)

    Returns:
        Number of affected rows.
    """
    logger.debug(f"Inserting summaries batch of size: {len(data)}")
    return execute_batch_insert(UPSERT_PROPOSITION_SUMMARY, data)


def insert_proposition_entities_batch(data: List[Tuple[int, str, str]]) -> int:
    """
    Insert a batch of named entities for propositions.

    Args:
        data: List of tuples (id, entity_type, entity)

    Returns:
        Number of affected rows.
    """
    logger.debug(f"Inserting entities batch of size: {len(data)}")
    return execute_batch_insert(UPSERT_PROPOSITION_NER, data)


def insert_authors_batch(data: List[Tuple[int, str, str, str]]) -> int:
    """
    Insert a batch of authors.

    Args:
        data: List of tuples (id, full_name, poli_party, uf)

    Returns:
        Number of affected rows.
    """
    logger.debug(f"Inserting authors batch of size: {len(data)}")
    return execute_batch_insert(UPSERT_AUTHORS, data)


def insert_proposition_topics_batch(rows: List[Tuple[int, str, float]]) -> None:
    """
    Insert or update proposition theme classifications in batch.

    Args:
        rows: List of tuples (id, theme).
    """
    if not rows:
        return

    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                psycopg2.extras.execute_values(
                    cur, UPSERT_PROPOSITION_TOPICS, 
                    rows, template=None, page_size=100)
    except Exception as exc:
        logger.exception("Failed to insert proposition topics batch: %s", exc)
        raise
    finally:
        conn.close()


def insert_propositions_batch(data: List[Tuple[int, str, str, str, List[int]]]) -> int:
    """
    Insert a batch of propositions.

    Args:
        data: List of tuples (id, url_full_text, proposition_type, submission_date, authors[])

    Returns:
        Number of affected rows.
    """
    logger.debug(f"Inserting propositions batch of size: {len(data)}")
    return execute_batch_insert(UPSERT_PROPOSITIONS, data)


def fetch_propositions_for_classification(limit: Optional[int] = None) -> List[Tuple[int, str]]:
    """
    Fetch propositions to be classified from the `propositions` table.

    Returns:
        A list of tuples (proposition_id, full_text). If the full text column is NULL,
        an empty string is returned for that record.
    """
    sql = """
    SELECT 
        id,
        text_summary
    FROM proposition_summary
    """
    params = ()
    if limit is not None:
        sql += " LIMIT %s"
        params = (limit,)

    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
                return [(int(r[0]), (r[1] or "")) for r in rows]
    except Exception as exc:
        logger.exception("Failed to fetch propositions for classification: %s", exc)
        raise
    finally:
        conn.close()

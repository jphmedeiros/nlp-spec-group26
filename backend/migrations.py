import logging
from data_extractor.db import get_db_connection

logger = logging.getLogger(__name__)


def create_tables() -> None:
    """
    Create required database tables for the data extractor, including
    the new proposition_themes table used to store theme classifications.
    """
    statements = [
        """
        CREATE TABLE IF NOT EXISTS proposition_word_cloud (
            id INTEGER NOT NULL,
            word TEXT NOT NULL,
            frequency INTEGER NOT NULL,
            PRIMARY KEY (id, word)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS proposition_summary (
            id INTEGER PRIMARY KEY,
            text_summary TEXT NOT NULL,
            main_theme TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            ideology TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS proposition_ner (
            id INTEGER NOT NULL,
            entity_type TEXT NOT NULL,
            entity TEXT NOT NULL,
            PRIMARY KEY (id, entity_type, entity)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS authors (
            id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            poli_party TEXT NOT NULL,
            uf TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS propositions (
            id INTEGER PRIMARY KEY,
            url_full_text TEXT NOT NULL,
            proposition_type TEXT NOT NULL,
            submission_date TIMESTAMP NOT NULL,
            authors INTEGER[] NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS proposition_topics (
            id BIGINT PRIMARY KEY,
            topic TEXT NOT NULL
        );
        """
    ]

    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                for sql in statements:
                    cur.execute(sql)
                    logger.debug("Executed migration SQL: %s", sql.splitlines()[0])
        logger.info("Database migrations applied successfully.")
    except Exception as exc:
        logger.exception("Failed to apply migrations: %s", exc)
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    # Allow running migrations as module: python -m data_extractor.migrations
    logging.basicConfig(level=logging.INFO)
    create_tables()

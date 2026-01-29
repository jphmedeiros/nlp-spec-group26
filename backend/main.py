#!/usr/bin/env python
# coding: utf-8

"""
Main entrypoint script that orchestrates data loading, DB inserts and LLM processing.
"""

from data_extractor.extractor import (
    load_propositions_dataset,
    extract_unique_authors,
    extract_propositions,
    generate_and_insert_word_clouds,
)
from data_extractor.openai_service import create_openai_client
from data_extractor.use_cases import process_propositions_in_parallel, classify_and_store_proposition_topics
from data_extractor.repository import insert_authors_batch, insert_propositions_batch, fetch_propositions_for_classification

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """
    Main orchestration function:
      1. Load propositions dataset
      2. Extract and insert authors and propositions
      3. Generate and insert word clouds
      4. Process propositions with the LLM and persist summaries/entities
    """
    try:
        # 1. Load data
        logger.info("Loading propositions dataset...")
        df_authors, df_propositions_filtered, df_propositions = load_propositions_dataset()
        logger.info(f"Loaded {len(df_propositions)} propositions")

        # 2. Authors
        logger.info("Extracting and inserting authors...")
        authors = extract_unique_authors(df_authors)
        insert_authors_batch(authors)
        logger.info(f"Inserted {len(authors)} authors")

        # 3. Propositions
        logger.info("Extracting and inserting propositions...")
        propositions = extract_propositions(df_propositions_filtered)
        insert_propositions_batch(propositions)
        logger.info(f"Inserted {len(propositions)} propositions")

        # 4. Word clouds
        logger.info("Generating and inserting word clouds...")
        generate_and_insert_word_clouds(df_propositions)
        logger.info("Word clouds insertion completed")

        # 5. OpenAI processing
        logger.info("Creating OpenAI client...")
        client = create_openai_client()

        logger.info("Processing propositions with OpenAI...")
        process_propositions_in_parallel(client, df_propositions, max_workers=3)
        
        logger.info("Fetching propositions for topic classification...")
        props = fetch_propositions_for_classification()
        logger.info(f"Fetched {len(props)} propositions for classification")
        
        logger.info("Classifying and storing proposition topics...")
        classify_and_store_proposition_topics(client, propositions=props, max_workers=10)
        
        logger.info("Pipeline execution completed successfully!")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.exception(f"Pipeline execution failed: {e}")
        raise

if __name__ == "__main__":
    main()

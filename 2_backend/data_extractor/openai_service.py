import logging
from openai import OpenAI
from .config import OPENAI_API_KEY
from typing import Optional

logger = logging.getLogger(__name__)


def create_openai_client(api_key: Optional[str] = None) -> OpenAI:
    """
    Create and return an OpenAI client using the provided API key or the one from config.

    Args:
        api_key: Optional API key string. If omitted, uses OPENAI_API_KEY from config.

    Returns:
        An OpenAI client instance.
    """
    key = api_key or OPENAI_API_KEY
    if not key:
        logger.error("OPENAI_API_KEY is not set. Set it in .env or pass as parameter.")
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=key)

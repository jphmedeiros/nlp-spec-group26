from dotenv import load_dotenv
import os

# Load environment variables from .env if present
load_dotenv()

# Database settings (can be overridden by environment variables)
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# Validate critical database credentials
if not DB_NAME or not DB_USER or not DB_PASS:
    raise ValueError(
        "Critical database credentials not set. "
        "Please set DB_NAME, DB_USER, and DB_PASS environment variables."
    )

# OpenAI key must be provided via environment variable for security
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Local file paths
PROPOSITIONS_JSON = os.getenv("PROPOSITIONS_JSON", "./proposicoes.json")

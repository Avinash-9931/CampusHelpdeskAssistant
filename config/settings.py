"""
Configuration module for the AI-Powered Campus Helpdesk Assistant.
Loads environment variables, defines directory paths, and enforces system constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file from project root if it exists
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# Directories
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
PROCESSED_DIR = DATA_DIR / "processed"
DEMO_DIR = DATA_DIR / "demo"
PROMPTS_DIR = BASE_DIR / "prompts"
ASSETS_DIR = BASE_DIR / "assets"
EVALUATION_DIR = BASE_DIR / "evaluation"
DOCS_DIR = BASE_DIR / "docs"

# Ensure runtime directories exist
for directory in [DATA_DIR, UPLOADS_DIR, PROCESSED_DIR, DEMO_DIR, PROMPTS_DIR, ASSETS_DIR, EVALUATION_DIR, DOCS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Cache and Storage Files
KNOWLEDGE_BASE_FILE = PROCESSED_DIR / "knowledge_base.json"
EMBEDDINGS_CACHE_FILE = PROCESSED_DIR / "embeddings_cache.npy"
TEST_CASES_FILE = EVALUATION_DIR / "test_cases.csv"

# Model & API settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip()
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004").strip()

# Ingestion & Chunking parameters
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", os.getenv("MAX_UPLOAD_SIZE_MB", "15")))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
MAX_UPLOAD_SIZE_MB = MAX_UPLOAD_MB
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_BYTES

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

# Information Retrieval parameters
TOP_K = int(os.getenv("TOP_K", "4"))
MIN_RELEVANCE_SCORE = float(os.getenv("MIN_RELEVANCE_SCORE", os.getenv("SIMILARITY_THRESHOLD", "0.13")))
SIMILARITY_THRESHOLD = MIN_RELEVANCE_SCORE
DEFAULT_RETRIEVAL_METHOD = os.getenv("DEFAULT_RETRIEVAL_METHOD", "lexical").strip().lower()

# Question validation & Conversation history parameters
MAX_QUESTION_CHARS = int(os.getenv("MAX_QUESTION_CHARS", "1000"))
HISTORY_TURNS = int(os.getenv("HISTORY_TURNS", "5"))


def has_api_key() -> bool:
    """
    Checks whether a non-empty Gemini API key is configured.
    Never prints or logs the key.
    """
    return bool(GEMINI_API_KEY and GEMINI_API_KEY.strip())


# Metadata & Attribution
PROJECT_METADATA = {
    "title": "AI-Powered Campus Helpdesk Assistant",
    "problem_statement": "C1 | Course: SCSE4041 – Prompt Engineering | Milestone 2",
    "team": "Invictus",
    "team_id": "PE-B01-15",
    "members": [
        {"name": "Kushagra Varshney", "id": "S24CSEU0060"},
        {"name": "Lakshay Bhatia", "id": "S24CSEU0062"},
        {"name": "Shivendra Singh", "id": "S24CSEU0416"},
        {"name": "Avinash Kumar", "id": "S24CSEU0709", "role": "Primary Developer (Backend & Chatbot)"},
        {"name": "Divyanshu Raj", "id": "S24CSEU0800", "role": "Primary Developer (Frontend, Integration & Testing)"},
        {"name": "Devvrat Arya", "id": "S24CSEU0866"},
    ],
}

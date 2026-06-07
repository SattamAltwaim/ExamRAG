import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

VOYAGE_API_KEY = os.environ["VOYAGE_API_KEY"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

CHROMA_DB_PATH = str(Path(__file__).resolve().parent / "chroma_store")
COLLECTION_NAME = "course_content"
EMBEDDING_MODEL = "voyage-3"
VLM_MODEL = "anthropic/claude-sonnet-4"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
CONTENT_DIR = str(Path(__file__).resolve().parent.parent / "Content")

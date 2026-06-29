import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-sonnet-4-6"

# Voyage AI
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
VOYAGE_MODEL = "voyage-3-lite"

# Google Drive
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
DRIVE_BASE_FOLDER_ID = "16mWWBNRdOlHt0PoOBMcY32NqN-3v4Fw5"
LIVE_FOLDER_NAME = "00_Live"
INBOX_FOLDER_NAME = "01_Minutes_Inbox"
ARCHIVE_FOLDER_NAME = "02_Archive"
DRAFTS_FOLDER_NAME = "03_Drafts"

# ChromaDB
CHROMA_PERSIST_DIR = "./chroma_db"
CHROMA_COLLECTION = "cat_minutes_archive"

# Retrieval
TOP_K_CHUNKS = 3
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

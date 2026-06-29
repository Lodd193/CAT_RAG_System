import os
from dotenv import load_dotenv

load_dotenv()


def _secret(key):
    """Read from st.secrets (Streamlit Cloud) with os.getenv fallback (local)."""
    try:
        import streamlit as st
        return st.secrets[key]
    except Exception:
        return os.getenv(key)


# App access
APP_PASSWORD = _secret("APP_PASSWORD")  # set in Streamlit secrets; if absent, auth is skipped (local dev)

# Anthropic
ANTHROPIC_API_KEY = _secret("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-sonnet-4-6"

# Voyage AI
VOYAGE_API_KEY = _secret("VOYAGE_API_KEY")
VOYAGE_MODEL = "voyage-3-lite"

# Google Drive
GOOGLE_SERVICE_ACCOUNT_JSON = _secret("GOOGLE_SERVICE_ACCOUNT_JSON")
DRIVE_BASE_FOLDER_ID = "16mWWBNRdOlHt0PoOBMcY32NqN-3v4Fw5"
LIVE_FOLDER_NAME = "00_Live"
INBOX_FOLDER_NAME = "01_Minutes_Inbox"
ARCHIVE_FOLDER_NAME = "02_Archive"
DRAFTS_FOLDER_NAME = "03_Drafts"

# Direct folder IDs — avoids querying the parent CAT folder at runtime,
# so the service account only needs access to these 4 folders (not the root).
LIVE_FOLDER_ID = "1RK_NTqo6MiWIvkrJ1lIctvSyOa5XQtwu"
INBOX_FOLDER_ID = "1sFACUuSK9unDQ-ESOHzYjgZw2-FiqebA"
ARCHIVE_FOLDER_ID = "1oGNjESkGENg6fiGNFz9wU7dn2aCKTSpW"
DRAFTS_FOLDER_ID = "1aM0ByO7YawWyZS__u4sH-58mFIfUTPMe"

# ChromaDB
CHROMA_PERSIST_DIR = "./chroma_db"
CHROMA_COLLECTION = "cat_minutes_archive"

# Retrieval
TOP_K_CHUNKS = 3
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

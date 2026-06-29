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

# ChromaDB
CHROMA_PERSIST_DIR = "./chroma_db"
CHROMA_COLLECTION = "cat_minutes_archive"

# Retrieval
TOP_K_CHUNKS = 3
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

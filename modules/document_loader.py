from modules.drive_client import list_files, read_file
import config

_SUPPORTED_MIME_TYPES = {
    "application/vnd.google-apps.document",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
    "text/markdown",
}


def load_live_documents():
    """Return a single context string containing all readable files from 00_Live."""
    files = list_files(config.LIVE_FOLDER_ID)

    sections = []
    skipped = []

    for f in files:
        if f["mimeType"] not in _SUPPORTED_MIME_TYPES:
            skipped.append(f["name"])
            continue
        try:
            content = read_file(f["id"], f["mimeType"])
            if content.strip():
                sections.append(f"=== {f['name']} ===\n{content.strip()}")
        except Exception as e:
            skipped.append(f"{f['name']} (error: {e})")

    context = "\n\n".join(sections)
    return context, skipped

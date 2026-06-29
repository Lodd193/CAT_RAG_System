from datetime import datetime

import streamlit as st

import config
from modules.document_loader import load_live_documents
from modules.drive_client import get_folder_id, list_files, read_file, move_file
from modules.drafter import create_docx, draft_document
from modules.extractor import extract_from_minutes
from modules.llm_client import stream_query
from modules.retriever import embed_and_store, search, archive_chunk_count

_DOC_TYPES = {
    "Stakeholder Update": [
        {"key": "audience", "label": "Audience", "placeholder": "e.g. Executive Leadership Team, Divisional Directors", "area": False},
        {"key": "key_message", "label": "Key message", "placeholder": "e.g. Programme on track; Band 3 recruitment risk resolved", "area": False},
        {"key": "period", "label": "Period covered", "placeholder": "e.g. June 2026", "area": False},
    ],
    "Board Paper Section": [
        {"key": "section_title", "label": "Section title", "placeholder": "e.g. Programme Status, Financial Update", "area": False},
        {"key": "key_message", "label": "Key message", "placeholder": "e.g. Three workstreams RAG green; one amber due to staffing", "area": False},
        {"key": "audience", "label": "Audience", "placeholder": "e.g. Programme Board, Trust Board", "area": False},
    ],
    "Agenda": [
        {"key": "meeting_name", "label": "Meeting name", "placeholder": "e.g. CAT Programme Board", "area": False},
        {"key": "meeting_date", "label": "Date and time", "placeholder": "e.g. 15 July 2026, 10:00–12:00", "area": False},
        {"key": "items", "label": "Key agenda items (one per line)", "placeholder": "Programme status update\nRAID log review\nStaffing update", "area": True},
    ],
    "Workstream Update": [
        {"key": "workstream", "label": "Workstream name", "placeholder": "e.g. Band 3 Admin Restructure", "area": False},
        {"key": "period", "label": "Period", "placeholder": "e.g. June 2026", "area": False},
        {"key": "progress", "label": "Progress summary", "placeholder": "e.g. Recruitment on track, 3 of 5 posts filled", "area": False},
    ],
    "Action Log": [
        {"key": "meeting_name", "label": "Meeting name", "placeholder": "e.g. CAT Programme Board — June 2026", "area": False},
        {"key": "actions", "label": "Actions (one per line: description — owner — deadline)", "placeholder": "Circulate RAID log — Richard — 30 June\nConfirm IG sign-off — Matt — 7 July", "area": True},
    ],
}

st.set_page_config(page_title="CAT Programme Assistant", layout="wide")
st.title("CAT Programme Assistant")
st.caption("Clinical Administration Transformation — University Hospitals Birmingham")

# ── Authentication gate ────────────────────────────────────────────────────────
if config.APP_PASSWORD and not st.session_state.get("authenticated"):
    st.divider()
    pwd = st.text_input("Access password", type="password")
    if st.button("Sign in", type="primary"):
        if pwd == config.APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

mode = st.radio(
    "Select mode:",
    ["Ask a Question", "Process Minutes", "Draft Document"],
    horizontal=True,
)

st.divider()

# ── Ask a Question ─────────────────────────────────────────────────────────────
if mode == "Ask a Question":

    # Load live docs once per session
    if "live_context" not in st.session_state:
        with st.spinner("Loading programme documents from Google Drive…"):
            try:
                context, skipped = load_live_documents()
                st.session_state.live_context = context
                st.session_state.live_skipped = skipped
            except Exception as e:
                print(f"[ERROR] Drive load failed: {e}")
                st.error("Could not load documents from Google Drive. Try reloading, or contact the programme administrator.")
                st.stop()

    context = st.session_state.live_context
    skipped = st.session_state.live_skipped
    doc_count = context.count("=== ")

    archive_count = archive_chunk_count()
    st.caption(
        f"{doc_count} documents loaded from 00_Live  ·  "
        f"{archive_count} archive chunks in ChromaDB"
    )
    if skipped:
        st.warning(f"Skipped {len(skipped)} file(s): {', '.join(skipped)}")

    with st.form("query_form"):
        query = st.text_input(
            "Your question",
            placeholder="e.g. What are the current open risks on the RAID log?",
        )
        submitted = st.form_submit_button("Ask", type="primary")

    if submitted and query.strip():
        archive_chunks = search(query.strip())
        archive_text = "\n\n".join(
            f"[{c['doc_name']}]\n{c['text']}" for c in archive_chunks
        ) if archive_chunks else ""
        st.write_stream(stream_query(context, query.strip(), archive_text))

    if st.button("Reload documents"):
        st.session_state.pop("live_context", None)
        st.session_state.pop("live_skipped", None)
        st.rerun()

# ── Process Minutes ────────────────────────────────────────────────────────────
elif mode == "Process Minutes":

    st.subheader("Process Meeting Minutes")

    source = st.radio("Input method:", ["Paste text", "Select from Drive inbox"], horizontal=True)

    minutes_text = None
    inbox_file = None  # {id, name, mimeType} if loaded from Drive

    if source == "Paste text":
        minutes_text = st.text_area(
            "Paste meeting minutes here:",
            height=300,
            placeholder="Paste the full minutes text…",
        )
    else:
        if "inbox_files" not in st.session_state:
            with st.spinner("Checking Drive inbox…"):
                try:
                    inbox_id = get_folder_id(config.DRIVE_BASE_FOLDER_ID, config.INBOX_FOLDER_NAME)
                    st.session_state.inbox_files = list_files(inbox_id)
                    st.session_state.inbox_folder_id = inbox_id
                except Exception as e:
                    print(f"[ERROR] Inbox access failed: {e}")
                    st.error("Could not access the Drive inbox. Try reloading.")
                    st.session_state.inbox_files = []

        inbox_files = st.session_state.get("inbox_files", [])
        if not inbox_files:
            st.info("No files found in 01_Minutes_Inbox. Paste minutes text directly instead.")
        else:
            names = [f["name"] for f in inbox_files]
            chosen = st.selectbox("Select file:", names)
            inbox_file = next(f for f in inbox_files if f["name"] == chosen)

    if st.button("Extract", type="primary"):
        text_to_process = minutes_text
        if inbox_file:
            with st.spinner(f"Reading {inbox_file['name']}…"):
                try:
                    text_to_process = read_file(inbox_file["id"], inbox_file["mimeType"])
                except Exception as e:
                    print(f"[ERROR] Drive file read failed: {e}")
                    st.error("Could not read the selected file from Drive.")
                    text_to_process = None

        if not text_to_process or not text_to_process.strip():
            st.warning("No text to process.")
        else:
            with st.spinner("Extracting structured data…"):
                try:
                    extracted = extract_from_minutes(text_to_process)
                    st.session_state.extracted = extracted
                    st.session_state.minutes_raw = text_to_process
                    st.session_state.inbox_file = inbox_file
                    # Clear any previous confirm state
                    st.session_state.pop("archived", None)
                except Exception as e:
                    print(f"[ERROR] Extraction failed: {e}")
                    st.error("Extraction failed. Check that the minutes text is readable and try again.")

    # ── Review panel ──────────────────────────────────────────────────────────
    if "extracted" in st.session_state and "archived" not in st.session_state:
        ex = st.session_state.extracted
        st.divider()
        st.subheader("Review extracted items")
        st.caption(
            f"**{ex.get('meeting_title', 'Meeting')}** · {ex.get('meeting_date', 'Date unknown')}"
        )

        def _checklist(items, key_prefix):
            kept = []
            for item in items:
                label = (
                    f"{item['description']} — {item.get('owner','?')} by {item.get('deadline','TBC')}"
                    if isinstance(item, dict)
                    else item
                )
                if st.checkbox(label, value=True, key=f"{key_prefix}_{hash(label)}"):
                    kept.append(item)
            return kept

        decisions_keep = []
        if ex.get("decisions"):
            with st.expander(f"Decisions ({len(ex['decisions'])})", expanded=True):
                decisions_keep = _checklist(ex["decisions"], "dec")

        actions_keep = []
        if ex.get("actions"):
            with st.expander(f"Actions ({len(ex['actions'])})", expanded=True):
                actions_keep = _checklist(ex["actions"], "act")

        risks_keep = []
        if ex.get("risks"):
            with st.expander(f"Risks ({len(ex['risks'])})", expanded=True):
                risks_keep = _checklist(ex["risks"], "risk")

        raid_keep = []
        if ex.get("raid_updates"):
            with st.expander(f"RAID updates ({len(ex['raid_updates'])})", expanded=True):
                raid_keep = _checklist(ex["raid_updates"], "raid")

        cp_keep = []
        if ex.get("critical_path_changes"):
            with st.expander(f"Critical path changes ({len(ex['critical_path_changes'])})", expanded=True):
                cp_keep = _checklist(ex["critical_path_changes"], "cp")

        st.divider()
        doc_name = st.text_input(
            "Archive document name:",
            value=(
                st.session_state.inbox_file["name"]
                if st.session_state.get("inbox_file")
                else ex.get("meeting_title", "minutes") + "_" + ex.get("meeting_date", "undated")
            ),
        )

        col1, col2 = st.columns([1, 3])
        with col1:
            confirm = st.button("Confirm and Archive", type="primary")
        with col2:
            if st.button("Discard"):
                for key in ("extracted", "minutes_raw", "inbox_file"):
                    st.session_state.pop(key, None)
                st.rerun()

        if confirm:
            with st.spinner("Archiving and embedding…"):
                try:
                    # Embed in ChromaDB
                    doc_id = doc_name.replace(" ", "_")
                    chunks_stored = embed_and_store(doc_id, doc_name, st.session_state.minutes_raw)

                    # Move Drive file to archive if it came from inbox
                    if st.session_state.get("inbox_file"):
                        archive_id = get_folder_id(
                            config.DRIVE_BASE_FOLDER_ID, config.ARCHIVE_FOLDER_NAME
                        )
                        move_file(st.session_state.inbox_file["id"], archive_id)
                        # Refresh inbox list
                        st.session_state.pop("inbox_files", None)

                    st.session_state.archived = {
                        "doc_name": doc_name,
                        "chunks": chunks_stored,
                        "decisions": decisions_keep,
                        "actions": actions_keep,
                        "risks": risks_keep,
                        "raid_updates": raid_keep,
                        "critical_path_changes": cp_keep,
                    }
                    for key in ("extracted", "minutes_raw", "inbox_file"):
                        st.session_state.pop(key, None)
                    st.rerun()
                except Exception as e:
                    print(f"[ERROR] Archive failed: {e}")
                    st.error("Archiving failed. The document was not moved or embedded. Try again.")

    if "archived" in st.session_state:
        a = st.session_state.archived
        st.success(
            f"Archived **{a['doc_name']}** — {a['chunks']} chunks added to ChromaDB."
        )
        total = sum(
            len(a.get(k, []))
            for k in ("decisions", "actions", "risks", "raid_updates", "critical_path_changes")
        )
        st.caption(f"{total} items confirmed across all categories.")
        if st.button("Process another document"):
            st.session_state.pop("archived", None)
            st.rerun()

# ── Draft Document ─────────────────────────────────────────────────────────────
elif mode == "Draft Document":

    st.subheader("Draft a Document")

    doc_type = st.selectbox("Document type:", list(_DOC_TYPES.keys()))

    user_inputs = {}
    for field in _DOC_TYPES[doc_type]:
        if field["area"]:
            user_inputs[field["key"]] = st.text_area(
                field["label"], placeholder=field["placeholder"], height=120
            )
        else:
            user_inputs[field["key"]] = st.text_input(
                field["label"], placeholder=field["placeholder"]
            )

    if st.button("Draft", type="primary"):
        if not any(v.strip() for v in user_inputs.values()):
            st.warning("Fill in at least one field before drafting.")
        else:
            # Load live context if not already in session
            if "live_context" not in st.session_state:
                with st.spinner("Loading programme documents…"):
                    try:
                        context, _ = load_live_documents()
                        st.session_state.live_context = context
                        st.session_state.live_skipped = _
                    except Exception as e:
                        print(f"[ERROR] Drive load failed (draft mode): {e}")
                        st.error("Could not load documents from Google Drive. Try reloading.")
                        st.stop()
            with st.spinner("Drafting…"):
                try:
                    draft = draft_document(doc_type, user_inputs, st.session_state.live_context)
                    st.session_state.draft_text = draft
                    st.session_state.draft_type = doc_type
                except Exception as e:
                    print(f"[ERROR] Drafting failed: {e}")
                    st.error("Drafting failed. Try again, or contact the programme administrator.")

    if "draft_text" in st.session_state:
        st.divider()
        edited = st.text_area(
            "Review and edit draft:",
            value=st.session_state.draft_text,
            height=500,
            key="draft_editor",
        )
        today = datetime.now().strftime("%d_%m_%y")
        doc_slug = st.session_state.draft_type.replace(" ", "")
        filename = f"{today}_RL_{doc_slug}.docx"
        st.download_button(
            label=f"Download {filename}",
            data=create_docx(edited, title=st.session_state.draft_type),
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        if st.button("Clear draft"):
            st.session_state.pop("draft_text", None)
            st.session_state.pop("draft_type", None)
            st.rerun()

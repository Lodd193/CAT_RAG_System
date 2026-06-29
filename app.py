import streamlit as st

import config
from modules.document_loader import load_live_documents
from modules.drive_client import get_folder_id, list_files, read_file, move_file
from modules.llm_client import stream_query
from modules.extractor import extract_from_minutes
from modules.retriever import embed_and_store, search, archive_chunk_count

st.set_page_config(page_title="CAT Programme Assistant", layout="wide")
st.title("CAT Programme Assistant")
st.caption("Clinical Administration Transformation — University Hospitals Birmingham")

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
                st.error(f"Could not load documents from Drive: {e}")
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
                    st.error(f"Could not access inbox: {e}")
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
                    st.error(f"Could not read file: {e}")
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
                    st.error(f"Extraction failed: {e}")

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
                    st.error(f"Archive failed: {e}")

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
    st.info("Document drafting — coming in Week 3")

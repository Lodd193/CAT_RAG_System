import streamlit as st

from modules.document_loader import load_live_documents
from modules.llm_client import stream_query

st.set_page_config(page_title="CAT Programme Assistant", layout="wide")
# TEMP DEBUG — remove after confirming secrets work
import os; st.caption(f"DEBUG secrets keys: {list(st.secrets.keys()) if st.secrets else 'empty'} | ANTHROPIC env: {'set' if os.getenv('ANTHROPIC_API_KEY') else 'None'} | DRIVE env: {'set' if os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON') else 'None'}")
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

    # Load once per session — Drive call is slow, cache in session_state
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

    st.caption(f"{doc_count} documents loaded from 00_Live")
    if skipped:
        st.warning(f"Skipped {len(skipped)} file(s): {', '.join(skipped)}")

    with st.form("query_form"):
        query = st.text_input(
            "Your question",
            placeholder="e.g. What are the current open risks on the RAID log?",
        )
        submitted = st.form_submit_button("Ask", type="primary")

    if submitted and query.strip():
        st.write_stream(stream_query(context, query.strip()))

    if st.button("Reload documents"):
        st.session_state.pop("live_context", None)
        st.session_state.pop("live_skipped", None)
        st.rerun()

# ── Process Minutes ────────────────────────────────────────────────────────────
elif mode == "Process Minutes":
    st.info("Minutes processing — coming in Week 2")

# ── Draft Document ─────────────────────────────────────────────────────────────
elif mode == "Draft Document":
    st.info("Document drafting — coming in Week 3")

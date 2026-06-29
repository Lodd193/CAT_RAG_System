# CAT Programme RAG System — Project Plan

## Overview

A hosted Streamlit web application that serves as an AI-powered programme management assistant for the Clinical Administration Transformation (CAT) programme at University Hospitals Birmingham NHS Foundation Trust.

The system interrogates live programme documents, processes meeting minutes, and drafts new documents — all grounded in the CAT corpus stored in Google Drive.

---

## Stack

| Component | Technology | Purpose |
|---|---|---|
| Frontend | Streamlit | Browser-based UI, hosted on Streamlit Community Cloud |
| Backend | Python | All logic, API calls, document handling |
| LLM | Claude Sonnet 4.6 (Anthropic API) | Answering, extraction, drafting |
| Embeddings | Voyage AI (voyage-3-lite) | Document and query embedding for archive search |
| Vector Store | ChromaDB | Persistent local vector storage for archived minutes |
| Document Source | Google Drive API | Live document retrieval and file writing |
| Hosting | Streamlit Community Cloud (free) | Accessible from any device including mobile |

---

## Google Drive Folder Structure

```
CAT Programme/
├── 00_Live/          ← Always loaded into context on every query
├── 01_Minutes_Inbox/ ← Drop new minutes here; triggers processing mode
├── 02_Archive/       ← Processed minutes moved here after extraction
└── 03_Drafts/        ← System-generated documents saved here
```

**Base folder ID:** `16mWWBNRdOlHt0PoOOBMcY32NqN-3v4Fw5`

---

## Project File Structure

```
cat-rag/
├── app.py                    ← Streamlit entry point, mode routing
├── config.py                 ← API keys, folder IDs, model settings
├── requirements.txt          ← All dependencies
├── .env                      ← API keys (never committed)
├── .gitignore                ← Excludes .env, chroma_db/, __pycache__/
├── PLAN.md                   ← This file
├── README.md                 ← Setup instructions
│
├── modules/
│   ├── __init__.py
│   ├── drive_client.py       ← Google Drive read/write operations
│   ├── document_loader.py    ← Load live docs from 00_Live into context
│   ├── retriever.py          ← Voyage AI embeddings + ChromaDB search
│   ├── extractor.py          ← Process minutes, extract structured updates
│   ├── drafter.py            ← Document drafting logic and templates
│   └── llm_client.py         ← Claude API wrapper, streaming support
│
├── prompts/
│   ├── system.txt            ← Base system prompt and programme context
│   ├── query.txt             ← System prompt for Q&A mode
│   ├── extraction.txt        ← System prompt for minutes processing
│   └── drafting.txt          ← System prompt for document drafting
│
└── chroma_db/                ← Persisted vector store (gitignored)
```

---

## Three Modes

### Mode 1 — Ask a Question
- Live documents loaded into context in full on every query
- ChromaDB queried for relevant archived minutes chunks (top 3)
- Combined context passed to Claude Sonnet 4.6
- Answer streams back with source citations
- One-click copy of response

### Mode 2 — Process Minutes
- User uploads or pastes new meeting minutes
- Claude extracts: decisions, actions (owner + deadline), risks, RAID updates, critical path changes
- Structured output presented as a review list — user ticks, crosses, or edits each item
- On confirm: live documents updated, minutes moved to 02_Archive, minutes embedded into ChromaDB
- Nothing updates without explicit user approval

### Mode 3 — Draft Document
- User selects document type from a fixed list (agenda, stakeholder update, board paper section, workstream update, action log)
- User answers 2–3 focused questions (audience, key message, tone)
- Claude drafts using live documents as context
- Output appears in editable text area
- One-click save to 03_Drafts with filename convention: DD_MM_YY_RL_[DocType].docx

---

## Build Sequence

### Setup — Done
- [x] Scaffold directory structure (`app.py`, `config.py`, `modules/`, `prompts/`)
- [x] Create GitHub repo (private): https://github.com/Lodd193/CAT_RAG_System
- [x] Write `requirements.txt`, `.gitignore`, `.env.example`
- [x] Write placeholder prompt templates (`query.txt`, `extraction.txt`, `drafting.txt`, `system.txt`)
- [x] Stub all module files

### Week 1 — Working Query Mode
**Goal:** Ask a question, get a grounded answer with citations. Deployable and useful immediately.

Tasks:
- [x] Set up Google Cloud project, enable Drive API, generate service account credentials
- [x] Implement `drive_client.py` — list files, read file content (Docs, Docx, plain text, xlsx), move files, upload files
- [x] Implement `document_loader.py` — load all files from 00_Live folder into context string (82K chars, 16 docs)
- [x] Implement `llm_client.py` — Claude API wrapper with streaming
- [x] Refine `prompts/query.txt` — system prompt with programme context
- [x] Build `app.py` — Streamlit home screen with three mode buttons, Query mode UI
- [x] Deploy to Streamlit Community Cloud
- [x] Connect `.env` secrets via Streamlit Cloud secrets manager
- [x] End-to-end test: ask a question about the RAID log, verify correct answer — 16 docs loaded on Cloud, RAID queries return correct answers with citations

### Week 2 — Minutes Processing — Done
**Goal:** Paste minutes, review extracted updates, confirm, archive.

Tasks:
- [x] Implement `retriever.py` — Voyage AI client, embed documents, ChromaDB store and search
- [x] Index existing archived minutes into ChromaDB (if any exist)
- [x] Write `prompts/extraction.txt` — structured extraction prompt (decisions, actions, risks, RAID)
- [x] Implement `extractor.py` — call Claude, parse structured output, return review list
- [x] Build Process Minutes UI in `app.py` — upload/paste, review checklist, confirm button
- [x] Implement archive move in `drive_client.py` — move file from 01_Minutes_Inbox to 02_Archive
- [x] Implement ChromaDB ingestion on confirm — chunk, embed, store
- [x] End-to-end test: extraction and embedding pipelines verified locally; Voyage AI + ChromaDB working

### Week 3 — Document Drafting — Done
**Goal:** Select a document type, answer prompts, get a draft, save to Drive.

Tasks:
- [x] Write `prompts/drafting.txt` — NHS programme management drafting prompt; instructs Claude to use ## headings, **bold**, bullet lists; omit duplicate title header
- [x] Implement `drafter.py` — 5 doc types, Claude generation, `create_docx()` with full markdown→Word conversion: inline bold/italic, heading hierarchy, bullet/numbered lists, markdown tables → Word Table Grid, A4 margins, programme header block (title + CAT/UHB + date)
- [x] Build Draft Document UI in `app.py` — type selector with 2–3 tailored fields per type, editable output text area
- [x] Implement draft download — `.docx` download button with `DD_MM_YY_RL_[DocType].docx` filename convention
- [x] End-to-end test: drafting pipeline verified locally; inline bold, tables, headings all render correctly in Word

### Security Hardening — Partially done (session 29 Jun 2026)
**Goal:** Resolve all identified security findings before wider deployment.

Done in code:
- [x] Auth gate — password check in `app.py` before any UI; skipped if `APP_PASSWORD` not set (local dev). User added `APP_PASSWORD` to Streamlit secrets.
- [x] Error message sanitisation — all `st.error(f"...{e}")` replaced with generic user messages; full exception logged server-side via `print()` for Streamlit Cloud logs
- [x] Prompt injection guard — added to `prompts/extraction.txt`
- [x] Drive scope — hardcoded 4 folder IDs in `config.py`; removed all `get_folder_id()` calls from `app.py` and `document_loader.py` so service account no longer needs access to CAT root

**Pending — pick up next session:**
- [ ] **Drive sharing** — remove service account (`cat-rag-drive@cat-rag-system.iam.gserviceaccount.com`) from CAT root folder in Google Drive; share each of the 4 subfolders individually as Editor. Then run verification script to confirm ≤4 folders + contents visible.
- [ ] **Voyage AI DPA** — obtain and file Data Processing Agreement before wider deployment. Check voyageai.com legal/privacy section.
- [ ] **Delete secrets file** — `C:\Users\lod19\Desktop\streamlit_secrets_PASTE_THIS.txt` still may exist; delete it.
- [ ] **End-to-end test on deployed app** — test Draft Document mode + .docx download + password gate on Streamlit Cloud after Drive sharing is corrected.

### Week 4 — Polish
**Goal:** Production-ready, reliable, pleasant to use.

Tasks:
- [ ] Add inbox notification — detect files in 01_Minutes_Inbox on app load, surface banner
- [ ] Improve citations — show document name and section for every answer
- [ ] Prompt tuning — refine all three prompts based on real usage
- [ ] Loading states — spinners and progress indicators throughout
- [ ] Mobile usability check — verify all three modes work on phone browser
- [ ] README update — setup instructions for future reference

---

## Key Configuration

```python
# config.py (values loaded from .env)

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-sonnet-4-6"

# Voyage AI
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
VOYAGE_MODEL = "voyage-3-lite"

# Google Drive
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
DRIVE_BASE_FOLDER_ID = "16mWWBNRdOlHt0PoOOBMcY32NqN-3v4Fw5"
LIVE_FOLDER_NAME = "00_Live"
INBOX_FOLDER_NAME = "01_Minutes_Inbox"
ARCHIVE_FOLDER_NAME = "02_Archive"
DRAFTS_FOLDER_NAME = "03_Drafts"

# ChromaDB
CHROMA_PERSIST_DIR = "./chroma_db"
CHROMA_COLLECTION = "cat_minutes_archive"

# Retrieval
TOP_K_CHUNKS = 3
CHUNK_SIZE = 800        # tokens
CHUNK_OVERLAP = 100     # tokens
```

---

## Environment Variables Required

```
ANTHROPIC_API_KEY=
VOYAGE_API_KEY=
GOOGLE_SERVICE_ACCOUNT_JSON=   ← full JSON blob as a single string
```

---

## Risk and Data Governance

- No patient data is processed. All documents are programme management records.
- Claude API terms confirmed: data not used for training, 7-day log retention, UK IDTA transfer mechanism in place.
- Voyage AI: confirm DPA before production use.
- Do not use consumer claude.ai account for any CAT documents.
- Flag to SRO (Matt Metcalfe) and IG Business Partner before wider deployment.
- All AI-generated documents reviewed and owned by Richard Lodder before use.

---

## Filename Convention

All outputs saved to Google Drive follow: `DD_MM_YY_RL_[DocType].docx`

Examples:
- `28_06_26_RL_StakeholderUpdate.docx`
- `28_06_26_RL_BoardPaperSection.docx`
- `28_06_26_RL_WorkstreamUpdate.docx`

---

## Dependencies (requirements.txt)

```
anthropic
voyageai
chromadb
streamlit
google-api-python-client
google-auth
google-auth-httplib2
google-auth-oauthlib
python-dotenv
sentence-transformers
pypandoc
python-docx
```

---

## Switching the LLM Backend

The modular structure means swapping the LLM backend is a one-file change. To switch from Claude API to a local Ollama model:

```python
# llm_client.py — swap this block only
# From:
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
# To:
import ollama
# Everything else in the codebase stays identical
```

---

## Build Priority List

Ordered by what unlocks the most value fastest. Each item is a discrete session of work.

### P1 — Must do next (Week 1 blockers)

1. ~~**Google Cloud setup**~~ — Done. GCP project, Drive API, service account, credentials in `.env`.
2. ~~**`drive_client.py`**~~ — Done. Auth, list, read (Docs/Docx/xlsx/txt/md), move, upload, create folder.
3. ~~**`document_loader.py`**~~ — Done. Loads 16 documents from `00_Live`, 82K chars, 0 skipped.
4. ~~**`llm_client.py`**~~ — Done. Streaming wrapper via `client.messages.stream()`; yields text chunks for `st.write_stream()`.
5. ~~**Query mode in `app.py`**~~ — Done. Form input → Drive docs → `stream_query()` → `st.write_stream()`; docs cached in session_state.
6. ~~**Deploy to Streamlit Community Cloud**~~ — Done. Live at https://catragsys-3mtjf29vgngvmirraqmrp6.streamlit.app/ — 16 docs load, RAID queries verified.

### P2 — Week 2 (minutes processing)

7. ~~**`retriever.py`**~~ — Done. Voyage AI + ChromaDB; embed_and_store, search, archive_chunk_count.
8. ~~**`extractor.py`**~~ — Done. Claude extraction returning decisions/actions/risks/RAID JSON.
9. ~~**Minutes UI in `app.py`**~~ — Done. Paste/inbox source, review checklist, Confirm archives + embeds.
10. ~~**Archive move in `drive_client.py`**~~ — Done. move_file() moves inbox file to 02_Archive on confirm.

### P3 — Week 3 (document drafting) — Done

11. ~~**`drafter.py`**~~ — Done. 5 doc types, Claude generation, full markdown→Word docx (bold, tables, headings, A4, header block).
12. ~~**Draft UI in `app.py`**~~ — Done. Type selector, tailored fields, editable output, .docx download.
13. ~~**Drive write**~~ — Done as .docx download button (service accounts can't write to personal Drive).

### P3.5 — Security hardening (29 Jun 2026)

14. ~~**Auth gate**~~ — Done. APP_PASSWORD in Streamlit secrets; gate in app.py.
15. ~~**Error sanitisation**~~ — Done. Generic UI messages, full errors in server logs.
16. ~~**Prompt injection guard**~~ — Done. Instruction added to extraction.txt.
17. ~~**Drive scope (code)**~~ — Done. 4 folder IDs hardcoded; no CAT root queries.
18. **Drive scope (Drive sharing)** — PENDING. Remove service account from CAT root; share 4 subfolders individually. Verify with test script.
19. **Voyage AI DPA** — PENDING. Obtain before wider deployment.
20. **Delete Desktop secrets file** — PENDING.

### P4 — Polish (Week 4, do last)

14. Inbox banner — detect files in `01_Minutes_Inbox` on app load, surface alert.
15. Richer citations — show document name and section per answer chunk.
16. Prompt tuning — iterate all three prompts against real CAT documents.
17. Error handling — graceful failures for API errors and Drive permission issues.
18. Loading states — spinners throughout.
19. Mobile usability pass.

---

*Last updated: 29 June 2026 (evening)*
*Owner: Richard Lodder, Programme Director, CAT Programme, UHB*

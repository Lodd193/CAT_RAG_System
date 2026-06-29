from io import BytesIO

import anthropic
from docx import Document
from docx.shared import Pt

import config

_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
_PROMPT_PATH = "prompts/drafting.txt"


def draft_document(doc_type: str, user_inputs: dict, live_context: str) -> str:
    with open(_PROMPT_PATH, encoding="utf-8") as f:
        prompt = f.read().format(
            doc_type=doc_type,
            user_inputs="\n".join(f"{k}: {v}" for k, v in user_inputs.items()),
            context=live_context,
        )
    response = _client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def create_docx(text: str) -> bytes:
    doc = Document()
    for line in text.splitlines():
        stripped = line.rstrip()
        if stripped.startswith("### "):
            doc.add_heading(stripped[4:], level=3)
        elif stripped.startswith("## "):
            doc.add_heading(stripped[3:], level=2)
        elif stripped.startswith("# "):
            doc.add_heading(stripped[2:], level=1)
        elif stripped.startswith(("- ", "* ")):
            doc.add_paragraph(stripped[2:], style="List Bullet")
        else:
            p = doc.add_paragraph(stripped)
            p.style.font.size = Pt(11)
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()

import re
from datetime import datetime
from io import BytesIO

import anthropic
from docx import Document
from docx.shared import Cm, Pt

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


def _add_formatted_runs(paragraph, text: str) -> None:
    """Add runs to a paragraph, rendering **bold** and *italic* markers."""
    for match in re.finditer(r"\*\*(.+?)\*\*|\*(.+?)\*|([^*]+)", text):
        bold_text, italic_text, plain_text = match.group(1), match.group(2), match.group(3)
        if bold_text is not None:
            paragraph.add_run(bold_text).bold = True
        elif italic_text is not None:
            paragraph.add_run(italic_text).italic = True
        elif plain_text:
            paragraph.add_run(plain_text)


def create_docx(text: str, title: str = "") -> bytes:
    doc = Document()

    # A4 page, standard margins
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.54)
    section.right_margin = Cm(2.54)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)

    # Normal style: Calibri 11pt
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)

    # Document header block
    if title:
        heading = doc.add_heading(title, level=0)
        heading.paragraph_format.space_after = Pt(2)
        sub = doc.add_paragraph()
        sub.add_run("Clinical Administration Transformation (CAT) Programme").bold = True
        sub.add_run("  ·  University Hospitals Birmingham NHS Foundation Trust")
        sub.paragraph_format.space_after = Pt(2)
        date_p = doc.add_paragraph(datetime.now().strftime("%d %B %Y"))
        date_p.paragraph_format.space_after = Pt(14)

    for line in text.splitlines():
        stripped = line.rstrip()

        if stripped in ("---", "***", "___"):
            # Treat horizontal rules as a visual section gap
            spacer = doc.add_paragraph()
            spacer.paragraph_format.space_after = Pt(4)
        elif stripped.startswith("### "):
            h = doc.add_heading(stripped[4:], level=3)
            h.paragraph_format.space_before = Pt(8)
            h.paragraph_format.space_after = Pt(4)
        elif stripped.startswith("## "):
            h = doc.add_heading(stripped[3:], level=2)
            h.paragraph_format.space_before = Pt(12)
            h.paragraph_format.space_after = Pt(6)
        elif stripped.startswith("# "):
            h = doc.add_heading(stripped[2:], level=1)
            h.paragraph_format.space_before = Pt(14)
            h.paragraph_format.space_after = Pt(6)
        elif stripped.startswith(("- ", "* ")):
            p = doc.add_paragraph(style="List Bullet")
            _add_formatted_runs(p, stripped[2:])
            p.paragraph_format.space_after = Pt(3)
        elif re.match(r"^\d+\.\s", stripped):
            p = doc.add_paragraph(style="List Number")
            _add_formatted_runs(p, re.sub(r"^\d+\.\s+", "", stripped))
            p.paragraph_format.space_after = Pt(3)
        elif stripped == "":
            pass  # blank lines: rely on paragraph space_after for separation
        else:
            p = doc.add_paragraph()
            _add_formatted_runs(p, stripped)
            p.paragraph_format.space_after = Pt(6)

    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()

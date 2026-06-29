import json
import re

import anthropic

import config

_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

_PROMPT_PATH = "prompts/extraction.txt"


def extract_from_minutes(minutes_text: str) -> dict:
    """
    Extract structured data from meeting minutes using Claude.
    Returns dict with keys: meeting_title, meeting_date, decisions, actions,
    risks, raid_updates, critical_path_changes.
    """
    with open(_PROMPT_PATH, encoding="utf-8") as f:
        prompt = f.read().format(minutes=minutes_text)

    response = _client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()

    # Strip markdown code fences if Claude wraps the JSON
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)

    return json.loads(raw.strip())

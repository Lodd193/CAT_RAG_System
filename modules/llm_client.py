import anthropic
import config

_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

_PROMPT_PATH = "prompts/query.txt"


def _load_system_prompt(context: str, archive_chunks: str = "") -> str:
    with open(_PROMPT_PATH, encoding="utf-8") as f:
        template = f.read()
    return template.format(
        documents=context,
        archive_chunks=archive_chunks or "(none — archive search enabled from Week 2)",
    )


def stream_query(context: str, user_query: str, archive_chunks: str = ""):
    """Yield response text chunks. Use with Streamlit's st.write_stream()."""
    system_prompt = _load_system_prompt(context, archive_chunks)
    with _client.messages.stream(
        model=config.CLAUDE_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_query}],
    ) as stream:
        for text in stream.text_stream:
            yield text

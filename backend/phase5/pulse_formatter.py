"""
Pulse Formatter — renders final Markdown and enforces ≤250-word limit (Phase 5).

Takes the raw Markdown from Gemini, prepends the standard header with
week label and review count, and truncates to 250 words if needed.
"""

import re
from datetime import datetime
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)

MAX_WORDS = 250


def _truncate_to_word_limit(text: str, max_words: int = MAX_WORDS) -> str:
    """
    Truncate text to max_words at a sentence boundary.

    If the text exceeds max_words, cuts at the last full sentence
    that fits within the limit. Falls back to hard word cutoff.
    """
    words = text.split()
    if len(words) <= max_words:
        return text

    logger.warning(
        f"Pulse exceeds {max_words}-word limit ({len(words)} words). Truncating..."
    )

    # Join first max_words and find last sentence boundary
    truncated = " ".join(words[:max_words])
    # Find last sentence-ending punctuation
    last_period = max(truncated.rfind(". "), truncated.rfind(".\n"))
    last_exclam = max(truncated.rfind("! "), truncated.rfind("!\n"))
    last_question = max(truncated.rfind("? "), truncated.rfind("?\n"))
    last_boundary = max(last_period, last_exclam, last_question)

    if last_boundary > len(truncated) // 2:
        # Cut at sentence boundary if it's past the halfway point
        truncated = truncated[: last_boundary + 1]
    else:
        # Hard cutoff with ellipsis
        truncated = " ".join(words[:max_words]) + "..."

    return truncated


def format_pulse(
    raw_markdown: str,
    total_reviews: int,
    quotes: list[str] | None = None,
    week_label: str | None = None,
) -> str:
    """
    Format the raw Gemini Markdown into the final pulse document.

    Args:
        raw_markdown: Raw Markdown string from Gemini.
        total_reviews: Total number of reviews analysed.
        quotes: List of verbatim user quotes to inject as "User Voices".
        week_label: Week label string (e.g. "10 Mar 2026"). Auto-generated if None.

    Returns:
        Formatted Markdown string with header, within 250-word limit.
    """
    if not week_label:
        week_label = datetime.now().strftime("%d %b %Y")

    header = (
        f"## 📊 Groww Weekly App Review Pulse\n"
        f"**Week of {week_label} | {total_reviews} reviews analysed**\n\n"
    )

    # Enforce word limit on the body (excluding header and quotes)
    # We pass the raw markdown because the `markdown` package needs the `*` and `**`
    # symbols to correctly generate HTML lists (<ul><li>) and bold tags (<strong>).
    body = _truncate_to_word_limit(raw_markdown.strip())

    # Build User Voices section from the selected quotes
    quotes_section = ""
    if quotes:
        # Separate quotes with a blank line so `markdown` package forms distinct <p> tags
        quote_lines = "\n\n".join(f'> "{q}"' for q in quotes)
        quotes_section = f"\n\n### User Voices\n{quote_lines}"

    pulse_md = header + body + quotes_section
    word_count = len(pulse_md.split())
    logger.info(f"Final pulse: {word_count} words")

    return pulse_md



def save_pulse(pulse_md: str, output_path: Path) -> Path:
    """
    Save the formatted pulse Markdown to disk.

    Args:
        pulse_md: The formatted Markdown content.
        output_path: Path to write the file (e.g. data/processed/weekly_pulse.md).

    Returns:
        The output Path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(pulse_md, encoding="utf-8")
    logger.info(f"Saved weekly pulse to {output_path}")
    return output_path

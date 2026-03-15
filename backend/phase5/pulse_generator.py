"""
Pulse Generator — calls Google Gemini to produce the weekly pulse (Phase 5).

Uses the Gemini free-tier models (per ARCHITECTURE.md) to generate a structured
≤250-word weekly app review pulse from the top themes and user quotes.

Model fallback chain: gemini-2.5-flash → gemini-2.5-flash-lite → gemini-3.1-flash-lite
"""

import time
from typing import Any

from google import genai
from google.genai import types

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# Gemini free-tier models (per ARCHITECTURE.md), tried in order
MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite",
]
TEMPERATURE = 0.3
RETRY_ATTEMPTS = 3
BACKOFF_BASE = 1  # seconds

PULSE_PROMPT = """You are a product insight writer. Write a weekly app review pulse for Groww.

Top 3 Themes (by frequency):
{top_3_themes}

User Quotes (do NOT modify):
{three_quotes}

Write:
1. A 2-sentence executive summary
2. A section titled "Key Themes" featuring EXACTLY 3 distinct bullet points (one for each theme). 
   - MUST format as: * **Theme Name**: Description
   - MUST use a double newline `\\n\\n` between bullets so they do not merge.
3. 3 actionable improvement ideas for the product team

Rules:
- Total output ≤ 250 words
- No PII (no names, emails, IDs)
- Use clear, simple language
- Format in Markdown
"""


def _format_themes_for_prompt(
    theme_frequency: list[dict[str, Any]],
    themes_lookup: dict[str, dict[str, Any]],
    top_n: int = 3,
) -> str:
    """Format the top N themes into readable text for the prompt."""
    lines = []
    for entry in theme_frequency[:top_n]:
        tid = entry.get("theme_id", "")
        name = entry.get("theme_name", tid)
        pct = entry.get("share_pct", 0)
        theme_data = themes_lookup.get(tid, {})
        sentiment = theme_data.get("sentiment", "mixed")
        description = theme_data.get("description", "")
        
        # Emoji mapping
        if sentiment == "negative":
            emoji = "🔴"
        elif sentiment == "positive":
            emoji = "🟢"
        else:
            emoji = "🟡"
            
        lines.append(f"{emoji} {name} ({pct}%)\n{description}")
    return "\n\n".join(lines)


def _format_quotes_for_prompt(quotes: list[str]) -> str:
    """Format quotes as blockquote strings."""
    return "\n".join(f'> "{q}"' for q in quotes)


def generate_pulse(
    theme_frequency: list[dict[str, Any]],
    themes: list[dict[str, Any]],
    quotes: list[str],
) -> str:
    """
    Call Gemini to generate the weekly pulse Markdown.

    Tries each model in the MODELS fallback chain. For each model,
    retries up to RETRY_ATTEMPTS with exponential backoff.

    Args:
        theme_frequency: Sorted list of theme frequency dicts.
        themes: List of theme dicts (from themes.json).
        quotes: List of 3 verbatim user quote strings.

    Returns:
        Raw Markdown string from Gemini.

    Raises:
        RuntimeError: If all models and retry attempts fail.
    """
    # Build lookup: theme_id → theme dict
    themes_lookup = {t["theme_id"]: t for t in themes}

    prompt = PULSE_PROMPT.format(
        top_3_themes=_format_themes_for_prompt(theme_frequency, themes_lookup),
        three_quotes=_format_quotes_for_prompt(quotes),
    )

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    last_error = None
    for model_name in MODELS:
        logger.info(f"Trying Gemini model: {model_name}...")
        for attempt in range(RETRY_ATTEMPTS):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=TEMPERATURE,
                    ),
                )
                content = response.text.strip()
                if content:
                    logger.info(
                        f"Gemini ({model_name}) returned {len(content.split())} words."
                    )
                    return content
                last_error = ValueError("Empty response from Gemini")
            except Exception as e:
                last_error = e
                if attempt < RETRY_ATTEMPTS - 1:
                    delay = BACKOFF_BASE * (2 ** attempt)
                    logger.warning(
                        f"{model_name} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.warning(
                        f"{model_name} failed after {RETRY_ATTEMPTS} attempts. "
                        f"Trying next model..."
                    )

    raise RuntimeError(
        f"Gemini pulse generation failed with all models {MODELS}: {last_error}"
    )

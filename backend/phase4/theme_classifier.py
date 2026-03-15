"""
Theme Classifier — Groq zero-shot review → theme classification (Phase 4).

Classifies each review in a batch into exactly one theme_id.
Batch size: 50 reviews/call. 200ms delay between calls for rate limits.
"""

import json
import re
import time
from typing import Any

from groq import Groq

from config import settings
from models.theme import Theme
from utils.logger import get_logger

logger = get_logger(__name__)

# Same model as Phase 3 (Groq free tier)
MODEL = "llama-3.3-70b-versatile"
TEMPERATURE = 0.2
MAX_TOKENS = 2048
RETRY_ATTEMPTS = 3
BACKOFF_BASE = 1
BATCH_DELAY_SEC = 0.2

CLASSIFICATION_PROMPT = """Given the following themes:
{themes_json}

Classify each review below into exactly one theme_id.
Return a JSON array with one object per review: [{{"review_id": "...", "theme_id": "..."}}]
Use the exact review_id values from the list (e.g. rev_0001). Use only theme_ids from the themes above (e.g. T1, T2).
Return only the JSON array, no other text.

Reviews:
{batch_reviews}
"""


def _extract_json_from_response(content: str) -> list:
    """Extract a JSON array from LLM response."""
    if not content or not content.strip():
        raise ValueError("Empty response")
    text = content.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("["), text.rfind("]")
        if start != -1 and end != -1 and end > start:
            parsed = json.loads(text[start : end + 1])
        else:
            raise
    if not isinstance(parsed, list):
        raise ValueError(f"Expected JSON array, got {type(parsed)}")
    return parsed


def _format_themes_for_prompt(themes: list[Theme]) -> str:
    """Format themes as JSON for the prompt."""
    data = [{"theme_id": t.theme_id, "theme_name": t.theme_name, "description": t.description} for t in themes]
    return json.dumps(data, indent=2, ensure_ascii=False)


def _format_batch_for_prompt(batch: list[dict]) -> str:
    """Format a batch of reviews for the prompt (review_id + text)."""
    lines = []
    for r in batch:
        rid = r.get("id", "?")
        text = (r.get("text") or "").strip()
        if rid:
            lines.append(f"[{rid}] {text}")
    return "\n".join(lines) if lines else "(No reviews)"


def _call_groq(prompt: str) -> str:
    """Call Groq API and return assistant content."""
    client = Groq(api_key=settings.GROQ_API_KEY)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )
    return (response.choices[0].message.content or "").strip()


def classify_batch(batch: list[dict], themes: list[Theme]) -> list[dict]:
    """
    Classify one batch of reviews into theme_ids.

    Returns list of {"review_id": str, "theme_id": str}.
    Retries up to RETRY_ATTEMPTS with exponential backoff on parse failure.
    """
    theme_ids = {t.theme_id.upper() if t.theme_id else "" for t in themes}
    theme_ids = {x for x in theme_ids if x}
    prompt = CLASSIFICATION_PROMPT.format(
        themes_json=_format_themes_for_prompt(themes),
        batch_reviews=_format_batch_for_prompt(batch),
    )
    last_error = None
    for attempt in range(RETRY_ATTEMPTS):
        try:
            content = _call_groq(prompt)
            raw = _extract_json_from_response(content)
            result = []
            for item in raw:
                if not isinstance(item, dict):
                    continue
                rid = item.get("review_id") or item.get("id")
                tid = (item.get("theme_id") or "").strip().upper()
                if not rid:
                    continue
                # Ensure theme_id is one of the known themes
                if tid not in theme_ids and theme_ids:
                    tid = next(iter(theme_ids))
                result.append({"review_id": str(rid), "theme_id": tid})
            if result:
                return result
            last_error = ValueError("Empty classification result")
        except Exception as e:
            last_error = e
            if attempt < RETRY_ATTEMPTS - 1:
                delay = BACKOFF_BASE * (2**attempt)
                logger.warning(f"Classification attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
    logger.error(f"Batch classification failed after {RETRY_ATTEMPTS} attempts: {last_error}")
    return []


def classify_all(batches: list[list[dict]], themes: list[Theme]) -> list[dict]:
    """
    Classify all batches; returns flat list of {"review_id", "theme_id"}.
    Uses 200ms delay between batch calls per ARCHITECTURE.
    """
    all_classified = []
    for i, batch in enumerate(batches):
        logger.info(f"Classifying batch {i + 1}/{len(batches)} ({len(batch)} reviews)...")
        classified = classify_batch(batch, themes)
        all_classified.extend(classified)
        if i < len(batches) - 1:
            time.sleep(BATCH_DELAY_SEC)
    return all_classified

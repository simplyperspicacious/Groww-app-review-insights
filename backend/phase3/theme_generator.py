"""
Theme Generator — Groq LLM theme extraction and aggregation (Phase 3).

Step 1: Per-batch theme extraction (each batch of 50 reviews -> candidate themes).
Step 2: Theme aggregation (all candidates -> 3-5 final themes).
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

# Groq deprecated llama3-70b-8192 (Aug 2025); use llama-3.3-70b-versatile
MODEL = "llama-3.3-70b-versatile"
TEMPERATURE = 0.2
MAX_TOKENS = 1024
RETRY_ATTEMPTS = 3
BACKOFF_BASE = 1  # 1s, 2s, 4s

BATCH_EXTRACTION_PROMPT = """You are a product analyst. Below are app reviews for Groww, a stock & mutual fund investing app.

Identify the major themes that appear in these reviews.
Return a JSON array with this structure:
[
  {{
    "theme_name": "<short name, max 4 words>",
    "description": "<one sentence describing the theme>",
    "sentiment": "positive|negative|mixed",
    "count": <number of reviews matching this theme in this batch>
  }}
]

Rules:
- No PII in descriptions
- Themes must be distinct and non-overlapping
- Return only the JSON array, no other text.

Reviews:
{batch_reviews}
"""

AGGREGATION_PROMPT = """You are a product analyst. Below are candidate themes extracted from multiple batches of Groww app reviews.

Merge and consolidate these into exactly 3 to 5 final themes.
Combine similar/overlapping themes. Keep the most representative name and description.
Return a JSON array with this exact structure:
[
  {{
    "theme_id": "T1",
    "theme_name": "<short name, max 4 words>",
    "description": "<one sentence describing the theme>",
    "sentiment": "positive|negative|mixed"
  }}
]

Rules:
- Max 5 themes, minimum 3 themes
- No PII
- Themes must be distinct
- Use theme_id T1, T2, T3, ... in order.
- Return only the JSON array, no other text.

Candidate themes from all batches:
{all_batch_themes}
"""

FALLBACK_THEMES = [
    {"theme_id": "T1", "theme_name": "App Experience", "description": "General feedback on app usability and experience.", "sentiment": "mixed"},
    {"theme_id": "T2", "theme_name": "Features & Functionality", "description": "Feedback on specific features and product capabilities.", "sentiment": "mixed"},
    {"theme_id": "T3", "theme_name": "Support & Onboarding", "description": "Customer support, KYC, and onboarding related feedback.", "sentiment": "mixed"},
]


def _extract_json_from_response(content: str) -> list:
    """Extract a JSON array from LLM response, handling markdown code blocks."""
    if not content or not content.strip():
        raise ValueError("Empty response")
    text = content.strip()
    # Try to find ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()
    # Try parse as-is
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # Try to find first [ and last ]
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            parsed = json.loads(text[start : end + 1])
        else:
            raise
    if not isinstance(parsed, list):
        raise ValueError(f"Expected JSON array, got {type(parsed)}")
    return parsed


def _format_batch_for_prompt(batch: list[dict]) -> str:
    """Format a batch of reviews as text for the prompt."""
    lines = []
    for r in batch:
        rid = r.get("id", "?")
        text = r.get("text", "").strip()
        if text:
            lines.append(f"[{rid}] {text}")
    return "\n".join(lines) if lines else "(No review text)"


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


def extract_themes_from_batch(batch: list[dict]) -> list[dict]:
    """
    Call Groq to extract candidate themes from one batch of reviews.

    Returns list of dicts with theme_name, description, sentiment, count.
    Retries up to RETRY_ATTEMPTS with exponential backoff on JSON parse failure.
    """
    prompt = BATCH_EXTRACTION_PROMPT.format(
        batch_reviews=_format_batch_for_prompt(batch),
    )
    last_error = None
    for attempt in range(RETRY_ATTEMPTS):
        try:
            content = _call_groq(prompt)
            candidates = _extract_json_from_response(content)
            if candidates:
                return candidates
            last_error = ValueError("Empty themes array")
        except Exception as e:
            last_error = e
            if attempt < RETRY_ATTEMPTS - 1:
                delay = BACKOFF_BASE * (2**attempt)
                logger.warning(f"Batch theme parse attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
    logger.error(f"Batch theme extraction failed after {RETRY_ATTEMPTS} attempts: {last_error}")
    return []


def aggregate_themes(all_candidates: list[dict]) -> list[Theme]:
    """
    Call Groq to merge candidate themes into 3-5 final themes.

    Retries up to RETRY_ATTEMPTS. On failure, returns fallback 3-theme minimal set.
    """
    # Format candidates for prompt (each may have theme_name, description, sentiment, count)
    themes_text = json.dumps(all_candidates, indent=2, ensure_ascii=False)
    prompt = AGGREGATION_PROMPT.format(all_batch_themes=themes_text)

    last_error = None
    for attempt in range(RETRY_ATTEMPTS):
        try:
            content = _call_groq(prompt)
            raw = _extract_json_from_response(content)
            themes = []
            for i, item in enumerate(raw):
                if not isinstance(item, dict):
                    continue
                theme_id = item.get("theme_id") or f"T{i + 1}"
                theme_name = item.get("theme_name", "Unknown")
                description = item.get("description", "")
                sentiment = item.get("sentiment", "mixed")
                if sentiment not in ("positive", "negative", "mixed"):
                    sentiment = "mixed"
                themes.append(
                    Theme(
                        theme_id=str(theme_id),
                        theme_name=str(theme_name)[:80],
                        description=str(description)[:500],
                        sentiment=sentiment,
                    )
                )
            if 3 <= len(themes) <= 5:
                return themes
            last_error = ValueError(f"Expected 3-5 themes, got {len(themes)}")
        except Exception as e:
            last_error = e
            if attempt < RETRY_ATTEMPTS - 1:
                delay = BACKOFF_BASE * (2**attempt)
                logger.warning(f"Aggregation attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)

    logger.warning(f"Theme aggregation failed after {RETRY_ATTEMPTS} attempts. Using fallback 3-theme set.")
    return [Theme(**t) for t in FALLBACK_THEMES]


def generate(batches: list[list[dict]]) -> list[Theme]:
    """
    Full theme generation: per-batch extraction then aggregation.

    Args:
        batches: List of review batches (each batch = list of review dicts with id, text).

    Returns:
        List of 3-5 Theme models.
    """
    all_candidates = []
    for i, batch in enumerate(batches):
        logger.info(f"Theme extraction batch {i + 1}/{len(batches)} ({len(batch)} reviews)...")
        candidates = extract_themes_from_batch(batch)
        all_candidates.extend(candidates)
        time.sleep(0.2)  # Small delay between batch calls for rate limit

    if not all_candidates:
        logger.warning("No candidate themes from batches. Using fallback.")
        return [Theme(**t) for t in FALLBACK_THEMES]

    logger.info(f"Aggregating {len(all_candidates)} candidate themes into 3-5 final themes...")
    return aggregate_themes(all_candidates)

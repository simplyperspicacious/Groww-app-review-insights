"""
Quote Selector — picks 3 representative verbatim user quotes via LLM (Phase 5).

For each of the top 3 themes (by frequency), sends candidate reviews
to Groq and asks it to pick the single most representative, insightful quote.
"""

import json
import re
import time
from typing import Any

from groq import Groq

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# Groq config (same as Phase 3/4)
MODEL = "llama-3.3-70b-versatile"
TEMPERATURE = 0.2
MAX_TOKENS = 512
RETRY_ATTEMPTS = 3
BACKOFF_BASE = 1

# Simple PII patterns to double-check quotes
_PII_PATTERNS = [
    re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),  # email
    re.compile(r"\b\d{10,}\b"),  # phone numbers (10+ digits)
]

QUOTE_SELECTION_PROMPT = """You are a product analyst selecting the most representative user quote for a specific theme.

Theme: {theme_name}
Theme description: {theme_description}

Below are user reviews classified under this theme. Pick the ONE review that:
1. Best represents the theme
2. Is specific and insightful (not generic like "good app" or "bad app")
3. Is written in clear English
4. Contains no personal information (names, emails, phone numbers)

Reviews:
{candidate_reviews}

Return ONLY a JSON object with this exact format (no other text):
{{"selected_review_id": "<the review id you chose>", "reason": "<one sentence explaining why>"}}
"""


def _is_pii_free(text: str) -> bool:
    """Return True if text does not match any PII pattern."""
    for pat in _PII_PATTERNS:
        if pat.search(text):
            return False
    return True


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


def _extract_json(content: str) -> dict:
    """Extract a JSON object from LLM response."""
    text = content.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            parsed = json.loads(text[start : end + 1])
        else:
            raise
    return parsed


def _select_quote_via_llm(
    theme_name: str,
    theme_description: str,
    candidates: list[dict[str, str]],
) -> str | None:
    """
    Ask Groq to pick the best quote from candidates for a given theme.

    Args:
        theme_name: Name of the theme.
        theme_description: Description of the theme.
        candidates: List of {"id": str, "text": str} dicts.

    Returns:
        The selected review text, or None if LLM fails.
    """
    # Format candidates for prompt (cap at 20 to fit context window)
    review_lines = []
    for c in candidates[:20]:
        review_lines.append(f"[{c['id']}] {c['text']}")
    candidate_text = "\n".join(review_lines)

    prompt = QUOTE_SELECTION_PROMPT.format(
        theme_name=theme_name,
        theme_description=theme_description,
        candidate_reviews=candidate_text,
    )

    # Lookup for fast retrieval
    text_by_id = {c["id"]: c["text"] for c in candidates}

    last_error = None
    for attempt in range(RETRY_ATTEMPTS):
        try:
            content = _call_groq(prompt)
            result = _extract_json(content)
            selected_id = result.get("selected_review_id", "")
            reason = result.get("reason", "")

            if selected_id in text_by_id:
                logger.info(f"    LLM selected [{selected_id}]: {reason}")
                return text_by_id[selected_id]
            else:
                last_error = ValueError(f"LLM returned unknown review_id: {selected_id}")
        except Exception as e:
            last_error = e
            if attempt < RETRY_ATTEMPTS - 1:
                delay = BACKOFF_BASE * (2 ** attempt)
                logger.warning(
                    f"    Quote selection attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)

    logger.warning(f"    LLM quote selection failed: {last_error}. Using fallback.")
    return None


def _fallback_pick(candidates: list[dict[str, str]]) -> str | None:
    """Simple heuristic fallback: pick the candidate closest to 40 words."""
    best = None
    best_diff = float("inf")
    for c in candidates:
        wc = len(c["text"].split())
        diff = abs(wc - 40)
        if 10 <= wc <= 80 and diff < best_diff:
            best = c["text"]
            best_diff = diff
    return best


def select_quotes(
    classified_reviews: list[dict[str, Any]],
    preprocessed_reviews: list[dict[str, Any]],
    theme_frequency: list[dict[str, Any]],
    themes: list[dict[str, Any]],
    top_n: int = 3,
) -> list[str]:
    """
    Select representative quotes — one per top theme, using LLM.

    Args:
        classified_reviews: List of {"review_id": str, "theme_id": str}.
        preprocessed_reviews: List of review dicts with "id" and "text" fields.
        theme_frequency: Sorted list of {"theme_id", "theme_name", "count", "share_pct"}.
        themes: List of theme dicts from themes.json.
        top_n: Number of top themes to select quotes for (default 3).

    Returns:
        List of up to `top_n` verbatim quote strings.
    """
    # Build review text lookup: review_id → text
    review_text_map: dict[str, str] = {}
    for r in preprocessed_reviews:
        rid = r.get("id", "")
        text = (r.get("text") or "").strip()
        if rid and text:
            review_text_map[rid] = text

    # Build theme → list of review_ids
    theme_reviews: dict[str, list[str]] = {}
    for c in classified_reviews:
        tid = c.get("theme_id", "")
        rid = c.get("review_id", "")
        if tid and rid:
            theme_reviews.setdefault(tid, []).append(rid)

    # Theme lookup for descriptions
    theme_lookup = {t.get("theme_id", ""): t for t in themes}

    # Top N themes by frequency (already sorted descending)
    top_themes = [t["theme_id"] for t in theme_frequency[:top_n]]

    quotes: list[str] = []
    for tid in top_themes:
        candidate_ids = theme_reviews.get(tid, [])
        theme_data = theme_lookup.get(tid, {})
        theme_name = theme_data.get("theme_name", tid)
        theme_desc = theme_data.get("description", "")

        # Build PII-free candidate list
        candidates = []
        for rid in candidate_ids:
            text = review_text_map.get(rid)
            if text and _is_pii_free(text) and len(text.split()) >= 5:
                candidates.append({"id": rid, "text": text})

        if not candidates:
            logger.warning(f"  {tid} ({theme_name}): no suitable candidates")
            continue

        logger.info(f"  {tid} ({theme_name}): {len(candidates)} candidates -> asking LLM...")

        # Try LLM selection
        quote = _select_quote_via_llm(theme_name, theme_desc, candidates)

        # Fallback if LLM fails
        if not quote:
            quote = _fallback_pick(candidates)

        if quote:
            quotes.append(quote)
        else:
            logger.warning(f"  {tid}: could not select any quote")

    logger.info(f"Selected {len(quotes)} user quotes for the pulse.")
    return quotes

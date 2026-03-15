"""
Language Filter — keeps only English reviews using langdetect.
"""

from typing import List, Dict, Any
from langdetect import detect, LangDetectException
from utils.logger import get_logger

logger = get_logger(__name__)


def filter_english(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Keep only reviews detected as English.

    Uses langdetect to classify review language. Reviews that fail detection
    (too short, ambiguous, etc.) are dropped as a safety measure.

    Args:
        reviews: List of review dictionaries (must have 'content' field).

    Returns:
        List of reviews detected as English.
    """
    english_reviews = []
    dropped_count = 0

    for review in reviews:
        text = review.get("content", "")
        if not text or not text.strip():
            dropped_count += 1
            continue

        try:
            lang = detect(text)
            if lang == "en":
                english_reviews.append(review)
            else:
                dropped_count += 1
        except LangDetectException:
            # Detection failed (too short, ambiguous) — drop the review
            dropped_count += 1

    logger.info(
        f"Language filter: {len(english_reviews)}/{len(reviews)} reviews are English "
        f"({dropped_count} non-English or undetectable dropped)"
    )
    return english_reviews

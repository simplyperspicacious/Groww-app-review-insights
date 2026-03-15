"""
Deduplicator — drops reviews with exact-duplicate text content.
"""

from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


def run(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove reviews with duplicate text content (keeps first occurrence).

    Args:
        reviews: List of review dictionaries (must have 'content' field).

    Returns:
        Deduplicated list of reviews.
    """
    seen_texts = set()
    unique_reviews = []
    duplicate_count = 0

    for review in reviews:
        text = review.get("content", "")
        # Normalise whitespace for comparison
        normalised = " ".join(text.split()).strip().lower()

        if normalised in seen_texts:
            duplicate_count += 1
            continue

        seen_texts.add(normalised)
        unique_reviews.append(review)

    logger.info(
        f"Deduplication: {duplicate_count}/{len(reviews)} duplicates removed "
        f"({len(unique_reviews)} unique reviews remaining)"
    )
    return unique_reviews

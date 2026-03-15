"""
Metadata Tagger — attaches week_number and rating_bucket to reviews.

Rating bucketing (ARCHITECTURE.md):
  1-2 -> negative
  3   -> neutral
  4-5 -> positive
"""

from datetime import datetime
from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)

BUCKET_NEGATIVE = "negative"
BUCKET_NEUTRAL = "neutral"
BUCKET_POSITIVE = "positive"


def rating_to_bucket(rating: int) -> str:
    """Map rating 1-5 to sentiment bucket."""
    if rating <= 2:
        return BUCKET_NEGATIVE
    if rating == 3:
        return BUCKET_NEUTRAL
    return BUCKET_POSITIVE


def date_to_week_number(date_str: str) -> int:
    """Get ISO week number from YYYY-MM-DD date string."""
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return dt.isocalendar()[1]
    except (ValueError, TypeError):
        return 0


def tag(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Add week_number and rating_bucket to each review.

    Expects each review to have "date" (YYYY-MM-DD) and "rating" (1-5).

    Args:
        reviews: List of review dicts.

    Returns:
        Same list with week_number and rating_bucket added.
    """
    for review in reviews:
        review["week_number"] = date_to_week_number(review.get("date", ""))
        review["rating_bucket"] = rating_to_bucket(review.get("rating", 3))
    logger.info(f"Metadata tagger: {len(reviews)} reviews tagged (week_number, rating_bucket)")
    return reviews

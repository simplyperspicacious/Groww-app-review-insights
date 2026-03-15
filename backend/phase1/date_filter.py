"""
Date Filter — keeps only reviews within the last N weeks from the run date.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


def apply(
    reviews: List[Dict[str, Any]],
    weeks: int = 12,
    run_date: datetime = None,
) -> List[Dict[str, Any]]:
    """
    Filter reviews to only keep those within the last N weeks.

    Args:
        reviews: List of review dictionaries (must have 'at' field as datetime or str).
        weeks: Number of weeks to look back (default: 12).
        run_date: Reference date for filtering (default: now).

    Returns:
        Filtered list of reviews within the date window.
    """
    run_date = run_date or datetime.now()
    cutoff_date = run_date - timedelta(weeks=weeks)
    filtered = []

    for review in reviews:
        review_date = review.get("at")
        if review_date is None:
            continue

        # Handle both datetime objects and ISO string formats
        if isinstance(review_date, str):
            try:
                review_date = datetime.fromisoformat(review_date)
            except ValueError:
                logger.warning(f"Unparseable date: {review_date}, skipping review")
                continue

        if review_date >= cutoff_date:
            filtered.append(review)

    logger.info(
        f"Date filter: {len(filtered)}/{len(reviews)} reviews within last {weeks} weeks "
        f"(cutoff: {cutoff_date.strftime('%Y-%m-%d')})"
    )
    return filtered

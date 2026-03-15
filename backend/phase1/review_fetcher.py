"""
Review Fetcher — fetches live reviews from Google Play Store using google-play-scraper.
"""

from typing import List, Dict, Any
from google_play_scraper import reviews, Sort
from utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


def fetch_reviews(
    app_id: str = None,
    count: int = None,
    lang: str = "en",
    country: str = "in",
) -> List[Dict[str, Any]]:
    """
    Fetch reviews from the Google Play Store.

    Args:
        app_id: Play Store package ID (default: from settings).
        count: Number of reviews to fetch (default: from settings).
        lang: Language code for reviews.
        country: Country code for the Play Store.

    Returns:
        List of raw review dictionaries from google-play-scraper.
    """
    app_id = app_id or settings.GROWW_PLAY_STORE_ID
    count = count or settings.DEFAULT_REVIEW_COUNT

    logger.info(f"Fetching up to {count} reviews for '{app_id}' (lang={lang}, country={country})")

    all_reviews: List[Dict[str, Any]] = []
    continuation_token = None

    # google-play-scraper returns max ~200 per call, so we loop
    while len(all_reviews) < count:
        batch_size = min(200, count - len(all_reviews))
        result, continuation_token = reviews(
            app_id,
            lang=lang,
            country=country,
            sort=Sort.NEWEST,
            count=batch_size,
            continuation_token=continuation_token,
        )

        if not result:
            logger.info("No more reviews returned by scraper.")
            break

        all_reviews.extend(result)
        logger.info(f"Fetched {len(result)} reviews (total so far: {len(all_reviews)})")

        if continuation_token is None:
            break

    logger.info(f"Total reviews fetched: {len(all_reviews)}")
    return all_reviews

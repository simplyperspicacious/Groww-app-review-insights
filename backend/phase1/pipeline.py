"""
Phase 1 Pipeline — Orchestrates the full Review Fetching & Data Ingestion pipeline.

Flow:
  1. Fetch live reviews from Google Play Store
  2. Scrub PII (emails, phones, URLs, userName, reviewId)
  3. Filter by date (last N weeks)
  4. Filter by language (English only)
  5. Remove emoji-containing reviews
  6. Deduplicate
  7. Validate & convert to CleanReview schema
  8. Save to data/processed/clean_reviews.json
"""

import json
from datetime import datetime
from pathlib import Path

from config import settings
from models.review import CleanReview
from utils.logger import get_logger

from phase1 import review_fetcher, pii_scrubber, date_filter, language_filter, emoji_filter, deduplicator

logger = get_logger("phase1.pipeline")

# Minimum word count for a review to be considered useful
MIN_WORD_COUNT = 5

# Backend root (parent of phase1/)
_BACKEND_ROOT = Path(__file__).resolve().parent.parent


def validate_and_convert(reviews: list, start_id: int = 1) -> list[CleanReview]:
    """
    Validate raw reviews and convert to CleanReview models.

    Validation rules (from ARCHITECTURE.md):
    - rating in [1, 5]
    - date parseable as ISO8601
    - text must have >= 5 words
    - title field is dropped entirely
    - platform hardcoded as "android"
    """
    clean_reviews = []
    skipped = 0

    for review in reviews:
        text = review.get("content", "")
        score = review.get("score")
        review_date = review.get("at")

        # Validate rating
        if score is None or not (1 <= score <= 5):
            skipped += 1
            continue

        # Validate text has >= 5 words
        if not text or len(text.split()) < MIN_WORD_COUNT:
            skipped += 1
            continue

        # Parse date
        if review_date is None:
            skipped += 1
            continue

        if isinstance(review_date, datetime):
            date_str = review_date.strftime("%Y-%m-%d")
        elif isinstance(review_date, str):
            try:
                datetime.fromisoformat(review_date)
                date_str = review_date[:10]
            except ValueError:
                skipped += 1
                continue
        else:
            skipped += 1
            continue

        # Build CleanReview
        review_id = f"rev_{start_id + len(clean_reviews):04d}"
        try:
            clean = CleanReview(
                id=review_id,
                rating=score,
                text=text,
                date=date_str,
                platform="android",
            )
            clean_reviews.append(clean)
        except Exception as e:
            logger.warning(f"Validation failed for review: {e}")
            skipped += 1

    logger.info(
        f"Validation: {len(clean_reviews)} valid, {skipped} skipped "
        f"(min {MIN_WORD_COUNT} words, valid rating & date)"
    )
    return clean_reviews


def run_pipeline(weeks: int = None, count: int = None) -> list[CleanReview]:
    """
    Execute the full Phase 1 pipeline.

    Args:
        weeks: Number of weeks to look back (default: from settings).
        count: Number of reviews to fetch (default: from settings).

    Returns:
        List of CleanReview objects.
    """
    weeks = weeks or settings.DEFAULT_WEEKS
    count = count or settings.DEFAULT_REVIEW_COUNT

    logger.info("=" * 60)
    logger.info("PHASE 1 PIPELINE — Starting")
    logger.info("=" * 60)

    # Step 1: Fetch reviews
    logger.info("[Step 1/6] Fetching reviews from Play Store...")
    raw_reviews = review_fetcher.fetch_reviews(count=count)
    logger.info(f"  -> Fetched {len(raw_reviews)} raw reviews")

    # Step 2: Scrub PII
    logger.info("[Step 2/6] Scrubbing PII...")
    reviews = pii_scrubber.clean(raw_reviews)

    # Step 3: Date filter
    logger.info(f"[Step 3/6] Filtering by date (last {weeks} weeks)...")
    reviews = date_filter.apply(reviews, weeks=weeks)

    # Step 4: Language filter
    logger.info("[Step 4/6] Filtering non-English reviews...")
    reviews = language_filter.filter_english(reviews)

    # Step 5: Emoji filter
    logger.info("[Step 5/6] Removing emoji-containing reviews...")
    reviews = emoji_filter.remove(reviews)

    # Step 6: Deduplication
    logger.info("[Step 6/6] Deduplicating...")
    reviews = deduplicator.run(reviews)

    # Validate and convert to CleanReview
    logger.info("Validating and converting to CleanReview schema...")
    clean_reviews = validate_and_convert(reviews)

    logger.info("=" * 60)
    logger.info(f"PHASE 1 COMPLETE — {len(clean_reviews)} clean reviews ready")
    logger.info("=" * 60)

    return clean_reviews


def save_results(clean_reviews: list[CleanReview], output_dir: str = None) -> Path:
    """Save clean reviews to data/processed/clean_reviews.json."""
    output_path = Path(output_dir) if output_dir else _BACKEND_ROOT / "data" / "processed"
    output_path.mkdir(parents=True, exist_ok=True)

    filepath = output_path / "clean_reviews.json"
    data = [review.model_dump() for review in clean_reviews]

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(data)} reviews to {filepath}")
    return filepath


if __name__ == "__main__":
    clean_reviews = run_pipeline()
    filepath = save_results(clean_reviews)
    print(f"\nDone! {len(clean_reviews)} clean reviews saved to: {filepath}")

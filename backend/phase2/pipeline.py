"""
Phase 2 Pipeline — Preprocessing & Text Enrichment.

Flow:
  1. Load clean_reviews.json (Phase 1 output)
  2. Normalise text (lowercase, strip HTML/markdown, remove special chars)
  3. Attach metadata (week_number, rating_bucket)
  4. Chunk into batches of 50
  5. Save preprocessed_reviews.json and review_batches/batch_001.json ...
"""

import json
from pathlib import Path

from models.review import PreprocessedReview
from utils.logger import get_logger

from phase2 import text_normaliser, metadata_tagger, batch_chunker

logger = get_logger("phase2.pipeline")

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_DATA_PROCESSED = _BACKEND_ROOT / "data" / "processed"
REVIEW_BATCHES_DIR = _DATA_PROCESSED / "review_batches"
DEFAULT_BATCH_SIZE = 50


def run_pipeline(
    input_path: Path = None,
    output_dir: Path = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> tuple[list[PreprocessedReview], list[list[dict]]]:
    """
    Execute the full Phase 2 pipeline.

    Args:
        input_path: Path to clean_reviews.json (default: data/processed/clean_reviews.json).
        output_dir: Directory for outputs (default: data/processed).
        batch_size: Reviews per batch (default 50).

    Returns:
        (list of PreprocessedReview, list of batches as list of dicts).
    """
    input_path = input_path or _DATA_PROCESSED / "clean_reviews.json"
    output_dir = output_dir or _DATA_PROCESSED

    logger.info("=" * 60)
    logger.info("PHASE 2 PIPELINE — Starting")
    logger.info("=" * 60)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Phase 1 output not found: {input_path}. Run Phase 1 first (python -m phase1.pipeline)."
        )

    # Load Phase 1 output
    logger.info(f"[Step 1/4] Loading {input_path}...")
    with open(input_path, encoding="utf-8") as f:
        reviews = json.load(f)
    logger.info(f"  -> Loaded {len(reviews)} clean reviews")

    # Normalise text
    logger.info("[Step 2/4] Normalising text...")
    reviews = text_normaliser.normalise(reviews, text_key="text")

    # Attach metadata (week_number, rating_bucket)
    logger.info("[Step 3/4] Tagging metadata (week_number, rating_bucket)...")
    reviews = metadata_tagger.tag(reviews)

    # Build PreprocessedReview models for validation
    preprocessed = []
    for r in reviews:
        try:
            preprocessed.append(
                PreprocessedReview(
                    id=r["id"],
                    rating=r["rating"],
                    text=r["text"],
                    date=r["date"],
                    platform=r.get("platform", "android"),
                    week_number=r["week_number"],
                    rating_bucket=r["rating_bucket"],
                )
            )
        except Exception as e:
            logger.warning(f"Skipping review {r.get('id')}: {e}")

    # Chunk into batches
    logger.info(f"[Step 4/4] Chunking into batches of {batch_size}...")
    batches = batch_chunker.chunk(reviews, batch_size=batch_size)

    logger.info("=" * 60)
    logger.info(f"PHASE 2 COMPLETE — {len(preprocessed)} preprocessed, {len(batches)} batches")
    logger.info("=" * 60)

    return preprocessed, batches


def save_results(
    preprocessed: list[PreprocessedReview],
    batches: list[list[dict]],
    output_dir: Path = None,
) -> tuple[Path, Path]:
    """
    Save preprocessed_reviews.json and review_batches/batch_001.json, ...

    Returns:
        (path to preprocessed_reviews.json, path to review_batches dir).
    """
    output_dir = output_dir or _DATA_PROCESSED
    output_dir.mkdir(parents=True, exist_ok=True)

    # preprocessed_reviews.json
    preprocessed_path = output_dir / "preprocessed_reviews.json"
    data = [p.model_dump() for p in preprocessed]
    with open(preprocessed_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(data)} reviews to {preprocessed_path}")

    # review_batches/
    batches_dir = output_dir / "review_batches"
    batches_dir.mkdir(parents=True, exist_ok=True)
    for i, batch in enumerate(batches, start=1):
        batch_path = batches_dir / f"batch_{i:03d}.json"
        with open(batch_path, "w", encoding="utf-8") as f:
            json.dump(batch, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(batches)} batches to {batches_dir}")

    return preprocessed_path, batches_dir


if __name__ == "__main__":
    preprocessed, batches = run_pipeline()
    preprocessed_path, batches_dir = save_results(preprocessed, batches)
    print(f"\nDone! {len(preprocessed)} preprocessed reviews -> {preprocessed_path}")
    print(f"      {len(batches)} batches -> {batches_dir}")

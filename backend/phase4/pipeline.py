"""
Phase 4 Pipeline — Review → Theme Classification (Groq Free Tier).

Flow:
  1. Load review batches from data/processed/review_batches/
  2. Load themes from data/processed/themes.json
  3. Classify each batch via Groq (zero-shot)
  4. Save classified_reviews.json and theme_frequency.json
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

from config import settings
from models.theme import Theme
from utils.logger import get_logger

from phase4 import theme_classifier

logger = get_logger("phase4.pipeline")

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_DATA_PROCESSED = _BACKEND_ROOT / "data" / "processed"
REVIEW_BATCHES_DIR = _DATA_PROCESSED / "review_batches"
THEMES_FILE = _DATA_PROCESSED / "themes.json"


def run_pipeline(
    batches_dir: Path = None,
    themes_path: Path = None,
    output_dir: Path = None,
) -> tuple[list[dict], list[dict], Path]:
    """
    Execute the full Phase 4 pipeline.

    Args:
        batches_dir: Directory with batch_001.json, ... (default: data/processed/review_batches).
        themes_path: Path to themes.json (default: data/processed/themes.json).
        output_dir: Where to write classified_reviews.json and theme_frequency.json.

    Returns:
        (classified_list, frequency_list, output_dir)
    """
    batches_dir = batches_dir or REVIEW_BATCHES_DIR
    themes_path = themes_path or THEMES_FILE
    output_dir = output_dir or _DATA_PROCESSED

    # Load phase4/.env for GROQ_API_KEY when running Phase 4 standalone
    _phase4_env = Path(__file__).resolve().parent / ".env"
    if _phase4_env.exists():
        load_dotenv(_phase4_env, override=True)
    settings.GROQ_API_KEY = os.getenv("GROQ_API_KEY", getattr(settings, "GROQ_API_KEY", "") or "")

    logger.info("=" * 60)
    logger.info("PHASE 4 PIPELINE — Review -> Theme Classification (Groq)")
    logger.info("=" * 60)

    if not (settings.GROQ_API_KEY or "").strip():
        raise ValueError(
            "GROQ_API_KEY is not set. Add it to .env (e.g. backend/phase4/.env or phase3/.env)."
        )

    if not batches_dir.exists():
        raise FileNotFoundError(
            f"Review batches not found: {batches_dir}. Run Phase 1 and Phase 2 first."
        )
    if not themes_path.exists():
        raise FileNotFoundError(
            f"Themes not found: {themes_path}. Run Phase 3 first."
        )

    # Load batches
    batch_files = sorted(batches_dir.glob("batch_*.json"))
    if not batch_files:
        raise FileNotFoundError(f"No batch_*.json files in {batches_dir}")

    batches = []
    for p in batch_files:
        with open(p, encoding="utf-8") as f:
            batches.append(json.load(f))

    # Load themes
    with open(themes_path, encoding="utf-8") as f:
        themes_data = json.load(f)
    themes = [Theme(**t) for t in themes_data]

    total_reviews = sum(len(b) for b in batches)
    logger.info(f"[Step 1/3] Loaded {len(batches)} batches ({total_reviews} reviews)")
    logger.info(f"[Step 2/3] Loaded {len(themes)} themes from {themes_path.name}")

    # Classify
    logger.info("[Step 3/3] Classifying reviews via Groq...")
    classified = theme_classifier.classify_all(batches, themes)

    # Compute theme frequency table (theme_id, theme_name, count, share_pct)
    theme_by_id = {t.theme_id: t for t in themes}
    counts = {}
    for c in classified:
        tid = c.get("theme_id", "")
        counts[tid] = counts.get(tid, 0) + 1
    total = len(classified) or 1
    frequency = []
    for tid, count in sorted(counts.items(), key=lambda x: -x[1]):
        theme = theme_by_id.get(tid)
        name = theme.theme_name if theme else tid
        pct = round(100 * count / total, 1)
        frequency.append({"theme_id": tid, "theme_name": name, "count": count, "share_pct": pct})

    output_dir.mkdir(parents=True, exist_ok=True)

    # Save classified_reviews.json
    classified_path = output_dir / "classified_reviews.json"
    with open(classified_path, "w", encoding="utf-8") as f:
        json.dump(classified, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(classified)} classifications to {classified_path.name}")

    # Save theme_frequency.json (for Phase 5 / reporting)
    frequency_path = output_dir / "theme_frequency.json"
    with open(frequency_path, "w", encoding="utf-8") as f:
        json.dump(frequency, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved theme frequency table to {frequency_path.name}")

    for row in frequency:
        logger.info(f"  {row['theme_id']} | {row['theme_name']} | {row['count']} | {row['share_pct']}%")

    logger.info("=" * 60)
    logger.info("PHASE 4 COMPLETE")
    logger.info("=" * 60)

    return classified, frequency, output_dir


if __name__ == "__main__":
    classified, frequency, out = run_pipeline()
    print(f"\nDone! {len(classified)} reviews classified. Output: {out}")

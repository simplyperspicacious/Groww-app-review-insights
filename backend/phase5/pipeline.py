"""
Phase 5 Pipeline — Weekly Pulse Generation (Gemini Free Tier).

Flow:
  1. Load Phase 4 outputs (classified_reviews, theme_frequency, themes, preprocessed_reviews)
  2. Select 3 representative user quotes (1 per top theme)
  3. Call Gemini to generate the weekly pulse
  4. Format Markdown and save to data/processed/weekly_pulse.md
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

from config import settings
from utils.logger import get_logger

from phase5 import quote_selector, pulse_generator, pulse_formatter

logger = get_logger("phase5.pipeline")

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_DATA_PROCESSED = _BACKEND_ROOT / "data" / "processed"

CLASSIFIED_REVIEWS_FILE = _DATA_PROCESSED / "classified_reviews.json"
THEME_FREQUENCY_FILE = _DATA_PROCESSED / "theme_frequency.json"
THEMES_FILE = _DATA_PROCESSED / "themes.json"
PREPROCESSED_REVIEWS_FILE = _DATA_PROCESSED / "preprocessed_reviews.json"
OUTPUT_FILE = _DATA_PROCESSED / "weekly_pulse.md"


def run_pipeline(
    classified_path: Path = None,
    frequency_path: Path = None,
    themes_path: Path = None,
    reviews_path: Path = None,
    output_path: Path = None,
) -> tuple[str, Path]:
    """
    Execute the full Phase 5 pipeline.

    Args:
        classified_path: Path to classified_reviews.json.
        frequency_path: Path to theme_frequency.json.
        themes_path: Path to themes.json.
        reviews_path: Path to preprocessed_reviews.json.
        output_path: Where to write weekly_pulse.md.

    Returns:
        (pulse_markdown, output_path)
    """
    classified_path = classified_path or CLASSIFIED_REVIEWS_FILE
    frequency_path = frequency_path or THEME_FREQUENCY_FILE
    themes_path = themes_path or THEMES_FILE
    reviews_path = reviews_path or PREPROCESSED_REVIEWS_FILE
    output_path = output_path or OUTPUT_FILE

    # Load GEMINI_API_KEY from phase3/.env or phase4/.env (shared .env files)
    for env_dir in ("phase3", "phase4"):
        env_file = _BACKEND_ROOT / env_dir / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=True)
    settings.GEMINI_API_KEY = os.getenv(
        "GEMINI_API_KEY", getattr(settings, "GEMINI_API_KEY", "") or ""
    )
    settings.GROQ_API_KEY = os.getenv(
        "GROQ_API_KEY", getattr(settings, "GROQ_API_KEY", "") or ""
    )

    logger.info("=" * 60)
    logger.info("PHASE 5 PIPELINE — Weekly Pulse Generation (Gemini)")
    logger.info("=" * 60)

    if not (settings.GEMINI_API_KEY or "").strip():
        raise ValueError(
            "GEMINI_API_KEY is not set. "
            "Add it to .env (e.g. backend/phase3/.env or backend/phase4/.env)."
        )
    if not (settings.GROQ_API_KEY or "").strip():
        raise ValueError(
            "GROQ_API_KEY is not set. "
            "Add it to .env (e.g. backend/phase3/.env or backend/phase4/.env)."
        )

    # Validate input files exist
    for label, path in [
        ("Classified reviews", classified_path),
        ("Theme frequency", frequency_path),
        ("Themes", themes_path),
        ("Preprocessed reviews", reviews_path),
    ]:
        if not path.exists():
            raise FileNotFoundError(
                f"{label} not found: {path}. Run previous phases first."
            )

    # Load data
    with open(classified_path, encoding="utf-8") as f:
        classified_reviews = json.load(f)
    with open(frequency_path, encoding="utf-8") as f:
        theme_frequency = json.load(f)
    with open(themes_path, encoding="utf-8") as f:
        themes = json.load(f)
    with open(reviews_path, encoding="utf-8") as f:
        preprocessed_reviews = json.load(f)

    total_reviews = len(preprocessed_reviews)

    logger.info(f"Loaded {total_reviews} preprocessed reviews")
    logger.info(f"Loaded {len(themes)} themes, {len(theme_frequency)} frequency entries")
    logger.info(f"Loaded {len(classified_reviews)} classified reviews")

    # Step 1: Select quotes
    logger.info("[Step 1/3] Selecting representative user quotes...")
    quotes = quote_selector.select_quotes(
        classified_reviews=classified_reviews,
        preprocessed_reviews=preprocessed_reviews,
        theme_frequency=theme_frequency,
        themes=themes,
        top_n=3,
    )

    if not quotes:
        logger.warning("No quotes selected — pulse will have empty User Voices section.")

    # Step 2: Generate pulse via Gemini
    logger.info("[Step 2/3] Generating pulse via Gemini...")
    raw_markdown = pulse_generator.generate_pulse(
        theme_frequency=theme_frequency,
        themes=themes,
        quotes=quotes,
    )

    # Step 3: Format and save
    logger.info("[Step 3/3] Formatting and saving pulse...")
    pulse_md = pulse_formatter.format_pulse(
        raw_markdown=raw_markdown,
        total_reviews=total_reviews,
        quotes=quotes,
    )
    pulse_formatter.save_pulse(pulse_md, output_path)

    logger.info("=" * 60)
    logger.info("PHASE 5 COMPLETE")
    logger.info("=" * 60)

    return pulse_md, output_path


if __name__ == "__main__":
    pulse, out = run_pipeline()
    print(f"\nDone! Weekly pulse saved to: {out}")

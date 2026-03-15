"""
Phase 3 Pipeline — LLM Theme Generation (Groq Free Tier).

Flow:
  1. Load review batches from data/processed/review_batches/
  2. Per-batch theme extraction via Groq (llama3-70b-8192)
  3. Theme aggregation into 3-5 final themes
  4. Save themes.json to data/processed/
"""

import json
from pathlib import Path

# Load phase3/.env first so GROQ_API_KEY is available (e.g. when run as python -m phase3.pipeline)
from dotenv import load_dotenv
_phase3_env = Path(__file__).resolve().parent / ".env"
if _phase3_env.exists():
    load_dotenv(_phase3_env, override=True)

from models.theme import Theme
from utils.logger import get_logger

from config import settings
from phase3 import theme_generator

logger = get_logger("phase3.pipeline")

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_DATA_PROCESSED = _BACKEND_ROOT / "data" / "processed"
REVIEW_BATCHES_DIR = _DATA_PROCESSED / "review_batches"


def run_pipeline(
    batches_dir: Path = None,
    output_dir: Path = None,
) -> tuple[list[Theme], Path]:
    """
    Execute the full Phase 3 pipeline.

    Args:
        batches_dir: Directory containing batch_001.json, batch_002.json, ... (default: data/processed/review_batches).
        output_dir: Directory for themes.json (default: data/processed).

    Returns:
        (themes, themes_filepath) — list of Theme models and path to saved themes.json.
    """
    batches_dir = batches_dir or REVIEW_BATCHES_DIR
    output_dir = output_dir or _DATA_PROCESSED

    # Ensure phase3/.env is loaded when running Phase 3 (e.g. GROQ_API_KEY)
    import os
    _phase3_env = Path(__file__).resolve().parent / ".env"
    if _phase3_env.exists():
        load_dotenv(_phase3_env, override=True)
    # Refresh settings in case .env was just loaded
    settings.GROQ_API_KEY = os.getenv("GROQ_API_KEY", getattr(settings, "GROQ_API_KEY", "") or "")

    logger.info("=" * 60)
    logger.info("PHASE 3 PIPELINE — LLM Theme Generation (Groq)")
    logger.info("=" * 60)

    if not (settings.GROQ_API_KEY or "").strip():
        raise ValueError(
            "GROQ_API_KEY is not set. Add it to .env (get a free key at https://console.groq.com)."
        )

    if not batches_dir.exists():
        raise FileNotFoundError(
            f"Review batches not found: {batches_dir}. Run Phase 1 and Phase 2 first."
        )

    # Load batches (batch_001.json, batch_002.json, ...)
    batch_files = sorted(batches_dir.glob("batch_*.json"))
    if not batch_files:
        raise FileNotFoundError(f"No batch_*.json files in {batches_dir}")

    batches = []
    for p in batch_files:
        with open(p, encoding="utf-8") as f:
            batches.append(json.load(f))

    logger.info(f"[Step 1/2] Loaded {len(batches)} batches ({sum(len(b) for b in batches)} total reviews)")

    # Generate themes (batch extraction + aggregation)
    logger.info("[Step 2/2] Theme extraction and aggregation via Groq...")
    themes = theme_generator.generate(batches)

    # Save themes.json per ARCHITECTURE output contract
    filepath = save_results(themes, output_dir)

    logger.info("=" * 60)
    logger.info(f"PHASE 3 COMPLETE — {len(themes)} themes generated")
    logger.info("=" * 60)

    return themes, filepath


def save_results(themes: list[Theme], output_dir: Path = None) -> Path:
    """Save themes to data/processed/themes.json."""
    output_dir = output_dir or _DATA_PROCESSED
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / "themes.json"
    data = [t.model_dump() for t in themes]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(data)} themes to {filepath}")
    return filepath


if __name__ == "__main__":
    themes, filepath = run_pipeline()
    print(f"\nDone! {len(themes)} themes saved to: {filepath}")

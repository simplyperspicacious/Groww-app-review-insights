"""
Phase 2 entry point — runs the Phase 2 pipeline (Preprocessing & Text Enrichment).

Requires Phase 1 output: data/processed/clean_reviews.json

Usage (from backend directory):
  python phase2_pipeline.py
  or
  python -m phase2.pipeline
"""

import sys
from pathlib import Path

_backend_root = Path(__file__).resolve().parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from phase2.pipeline import run_pipeline, save_results

if __name__ == "__main__":
    preprocessed, batches = run_pipeline()
    preprocessed_path, batches_dir = save_results(preprocessed, batches)
    print(f"\nDone! {len(preprocessed)} preprocessed reviews -> {preprocessed_path}")
    print(f"      {len(batches)} batches -> {batches_dir}")

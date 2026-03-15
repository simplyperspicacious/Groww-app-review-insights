"""
Phase 1 entry point — runs the Phase 1 pipeline (Review Fetching & Data Ingestion).

Usage (from backend directory):
  python phase1_pipeline.py
  or
  python -m phase1.pipeline
"""

import sys
from pathlib import Path

# Ensure backend root is on path when run as script
_backend_root = Path(__file__).resolve().parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from phase1.pipeline import run_pipeline, save_results

if __name__ == "__main__":
    clean_reviews = run_pipeline()
    filepath = save_results(clean_reviews)
    print(f"\nDone! {len(clean_reviews)} clean reviews saved to: {filepath}")

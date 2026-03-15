"""
Phase 3 entry point — LLM Theme Generation (Groq).

Requires: Phase 1 + Phase 2 run (data/processed/review_batches/*.json).
Requires: GROQ_API_KEY in .env

Usage (from backend directory):
  python phase3_pipeline.py
  or
  python -m phase3.pipeline
"""

import sys
from pathlib import Path

_backend_root = Path(__file__).resolve().parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

# Load phase3/.env so GROQ_API_KEY is available when running from here
from dotenv import load_dotenv
_load_env = _backend_root / "phase3" / ".env"
if _load_env.exists():
    load_dotenv(_load_env, override=True)

from phase3.pipeline import run_pipeline

if __name__ == "__main__":
    themes, filepath = run_pipeline()
    print(f"\nDone! {len(themes)} themes saved to: {filepath}")

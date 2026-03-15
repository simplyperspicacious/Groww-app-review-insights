"""
Phase 4 entry point — Review → Theme Classification (Groq).

Requires: Phase 1, 2, 3 run (review_batches/*.json and themes.json).
Requires: GROQ_API_KEY in .env (e.g. backend/phase4/.env or phase3/.env)

Usage (from backend directory):
  python phase4_pipeline.py
  or
  python -m phase4.pipeline
"""

import sys
from pathlib import Path

_backend_root = Path(__file__).resolve().parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from dotenv import load_dotenv
_load_env = _backend_root / "phase4" / ".env"
if _load_env.exists():
    load_dotenv(_load_env, override=True)

from phase4.pipeline import run_pipeline

if __name__ == "__main__":
    classified, frequency, out_dir = run_pipeline()
    print(f"\nDone! {len(classified)} reviews classified. Output dir: {out_dir}")

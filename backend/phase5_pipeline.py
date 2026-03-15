"""
Phase 5 entry point — Weekly Pulse Generation (Gemini).

Requires: Phase 1–4 run (data/processed/ files).
Requires: GEMINI_API_KEY in .env (e.g. backend/phase3/.env or backend/phase4/.env)

Usage (from backend directory):
  python phase5_pipeline.py
  or
  python -m phase5.pipeline
"""

import sys
from pathlib import Path

_backend_root = Path(__file__).resolve().parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

# Load .env from phase3/ or phase4/ (shared GEMINI_API_KEY)
from dotenv import load_dotenv
for _env_dir in ("phase3", "phase4"):
    _load_env = _backend_root / _env_dir / ".env"
    if _load_env.exists():
        load_dotenv(_load_env, override=True)

from phase5.pipeline import run_pipeline

if __name__ == "__main__":
    pulse, filepath = run_pipeline()
    print(f"\nDone! Weekly pulse saved to: {filepath}")

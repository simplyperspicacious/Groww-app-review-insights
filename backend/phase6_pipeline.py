"""
Standalone entry point for Phase 6.

Usage:
    python phase6_pipeline.py <recipient_email>

Reads environment variables across phase3/phase4/global .env
and sends the data/processed/weekly_pulse.md as an HTML email.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

from utils.logger import get_logger

# Add backend directory to sys.path so modules like `config` and `phase6` resolve correctly.
# This prevents ModuleNotFoundError when running this script individually.
_BACKEND_ROOT = Path(__file__).resolve().parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

# Load .env (Check phase3, phase4, and root)
for env_dir in ("phase3", "phase4", ""):
    env_file = _BACKEND_ROOT / env_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)

# Now we can safely import config and pipeline after setting up sys.path and env
from config import settings
from phase6.pipeline import run_pipeline


def main():
    recipient_email = None
    if len(sys.argv) >= 2:
        recipient_email = sys.argv[1].strip()
    
    if not recipient_email:
        recipient_email = os.getenv("TEST_RECIPIENT_EMAIL", "").strip()
        
    if not recipient_email:
        print("Usage: python phase6_pipeline.py <recipient_email>")
        print("Example: python phase6_pipeline.py your.manager@example.com")
        print("Or set TEST_RECIPIENT_EMAIL in your .env file.")
        sys.exit(1)
    
    # Ensure SMTP settings exist
    if not os.getenv("SMTP_USER") or not os.getenv("SMTP_PASSWORD"):
        print("ERROR: SMTP_USER or SMTP_PASSWORD not found in environment.")
        print("Please configure them in your .env file (e.g. backend/.env, phase3/.env).")
        print("If using Gmail, generate an 'App Password' for SMTP_PASSWORD.")
        sys.exit(1)

    # Logging is configured in utils.logger internally when get_logger is called
    
    try:
        run_pipeline(user_email=recipient_email)
    except Exception as e:
        print(f"\nPhase 6 Pipeline Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

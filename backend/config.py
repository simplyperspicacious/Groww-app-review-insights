"""
Configuration module — loads environment variables from .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Search for .env files in multiple places because they might be nested in phase dirs
_BACKEND_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _BACKEND_DIR.parent

for _env_path in (
    _PROJECT_ROOT / ".env",
    _BACKEND_DIR / ".env",
    _BACKEND_DIR / "phase3" / ".env",
    _BACKEND_DIR / "phase4" / ".env",
):
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path, override=True)


class Settings:
    """Application settings loaded from environment variables."""

    # Review Fetching (Groww's actual Play Store package ID)
    GROWW_PLAY_STORE_ID: str = os.getenv("GROWW_PLAY_STORE_ID", "com.nextbillion.groww")
    DEFAULT_REVIEW_COUNT: int = int(os.getenv("DEFAULT_REVIEW_COUNT", "500"))
    DEFAULT_WEEKS: int = int(os.getenv("DEFAULT_WEEKS", "12"))

    # Groq (Phase 3 & 4)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Gemini (Phase 5)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Gmail SMTP (Phase 6)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SENDER_NAME: str = os.getenv("SENDER_NAME", "Groww Insights Bot")
    
    # Brevo HTTP API (Optional Phase 6 Dispatcher for Render deployment)
    BREVO_API_KEY: str = os.getenv("BREVO_API_KEY", "")

    # GitHub Cache
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_REPO_OWNER: str = os.getenv("GITHUB_REPO_OWNER", "")
    GITHUB_REPO_NAME: str = os.getenv("GITHUB_REPO_NAME", "")
    GITHUB_BRANCH: str = os.getenv("GITHUB_BRANCH", "main")


settings = Settings()

"""
Main FastAPI server for App Review Insights Analyser.
Serves the Vanilla HTML/JS frontend and exposes the backend synthesis pipelines.
"""

import os
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

# Import existing pipelines
from phase5.pipeline import run_pipeline as run_phase5_pipeline
from phase6.pipeline import run_pipeline as run_phase6_pipeline
from utils.logger import get_logger

logger = get_logger(__name__)

# --- Configuration ---
_ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = _ROOT_DIR / "frontend"

app = FastAPI(
    title="Groww Pulse API",
    description="Backend API for the App Review Insights Analyser",
    version="1.0.0"
)

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class EmailRequest(BaseModel):
    recipient_email: EmailStr
    markdown_content: str


# --- API Endpoints ---
@app.post("/api/generate-pulse")
async def api_generate_pulse():
    """
    Executes Phase 1 through Phase 5 synchronously.
    Returns the generated Weekly Pulse markdown.
    """
    try:
        logger.info("Triggering Phase 1-5 pipeline via API...")
        # run_phase5_pipeline() actually executes Phase 1-4 internally as designed
        pulse_markdown, _ = run_phase5_pipeline()
        
        # We need total_reviews for the UI metadata. Since pipeline only returns the MD string,
        # we can quickly read the preprocessed length.
        reviews_path = Path(__file__).resolve().parent / "data" / "processed" / "preprocessed_reviews.json"
        total_reviews = 0
        if reviews_path.exists():
            import json
            with open(reviews_path, "r", encoding="utf-8") as f:
                total_reviews = len(json.load(f))
        
        return {
            "status": "success",
            "message": "Weekly Pulse generated successfully",
            "pulse_markdown": pulse_markdown,
            "total_reviews": total_reviews,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/send-email")
async def api_send_email(request: EmailRequest):
    """
    Executes Phase 6: Takes the markdown, builds an HTML email, and dispatches it via SMTP.
    """
    try:
        logger.info(f"Triggering Email Dispatch to {request.recipient_email}...")
        
        # We temporarily write the frontend's markdown to disk so phase6 can read it
        # (Since phase6 pipeline was originally designed to read from disk)
        temp_pulse_path = Path(__file__).resolve().parent / "data" / "processed" / "weekly_pulse.md"
        temp_pulse_path.parent.mkdir(parents=True, exist_ok=True)
        temp_pulse_path.write_text(request.markdown_content, encoding="utf-8")
        
        # Run Phase 6 dispatcher
        run_phase6_pipeline(user_email=request.recipient_email)
        
        return {
            "status": "success",
            "message": f"Email dispatched successfully to {request.recipient_email}"
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Email dispatch failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email. Check SMTP credentials.")


# --- Serve Frontend ---
# We mount the frontend dir to "/" so the user can just visit the root URL.
# Note: This MUST be the last route registered so it doesn't swallow /api requests.
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
else:
    logger.warning(f"Frontend directory not found at {FRONTEND_DIR}. UI will not load.")

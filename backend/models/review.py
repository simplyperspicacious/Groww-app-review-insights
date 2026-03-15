"""
Pydantic models for review data.
"""

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class RawReview(BaseModel):
    """Raw review as returned by google-play-scraper."""

    score: int = Field(..., ge=1, le=5, description="Rating 1-5")
    content: Optional[str] = Field(None, description="Review text body")
    at: Optional[str] = Field(None, description="Review date (ISO string or datetime)")
    userName: Optional[str] = Field(None, description="Reviewer username (PII — stripped)")
    reviewId: Optional[str] = Field(None, description="Google review ID (PII — stripped)")
    thumbsUpCount: Optional[int] = Field(0, description="Helpful votes count")


class CleanReview(BaseModel):
    """Cleaned, PII-free review ready for LLM processing."""

    id: str = Field(..., description="Internal review ID (e.g. rev_001)")
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5")
    text: str = Field(..., min_length=1, description="Cleaned review text")
    date: str = Field(..., description="Review date in YYYY-MM-DD format")
    platform: str = Field(default="android", description="Source platform (hardcoded)")

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Ensure date is valid ISO8601 format."""
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError(f"Invalid date format: {v}. Expected YYYY-MM-DD.")
        return v


class PreprocessedReview(BaseModel):
    """Review with normalised text and metadata for LLM consumption (Phase 2 output)."""

    id: str = Field(..., description="Internal review ID (e.g. rev_001)")
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5")
    text: str = Field(..., min_length=1, description="Normalised review text")
    date: str = Field(..., description="Review date in YYYY-MM-DD format")
    platform: str = Field(default="android", description="Source platform")
    week_number: int = Field(..., description="ISO week number of review date")
    rating_bucket: str = Field(
        ...,
        description="Sentiment bucket: negative (1-2), neutral (3), positive (4-5)",
    )

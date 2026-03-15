"""
Pydantic models for theme data (Phase 3 output).
"""

from pydantic import BaseModel, Field


class Theme(BaseModel):
    """Final consolidated theme (Phase 3 themes.json)."""

    theme_id: str = Field(..., description="Theme ID e.g. T1, T2")
    theme_name: str = Field(..., description="Short name, max 4 words")
    description: str = Field(..., description="One sentence describing the theme")
    sentiment: str = Field(
        ...,
        description="Sentiment: positive, negative, or mixed",
    )

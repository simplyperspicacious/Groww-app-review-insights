"""
Pydantic models for weekly pulse data (Phase 5 output).
"""

from pydantic import BaseModel, Field


class ThemeSummary(BaseModel):
    """Summary of a single theme for the weekly pulse."""

    theme_id: str = Field(..., description="Theme ID e.g. T1, T2")
    theme_name: str = Field(..., description="Short theme name")
    share_pct: float = Field(..., description="Percentage share of reviews")
    sentiment: str = Field(..., description="Sentiment: positive, negative, or mixed")
    summary_sentence: str = Field(..., description="One-sentence summary of the theme")


class WeeklyPulse(BaseModel):
    """Complete weekly pulse output (Phase 5 result)."""

    executive_summary: str = Field(..., description="2-sentence executive summary")
    theme_summaries: list[ThemeSummary] = Field(
        ..., description="Top 3 themes with summaries"
    )
    user_quotes: list[str] = Field(
        ..., description="3 representative verbatim user quotes (PII-free)"
    )
    action_ideas: list[str] = Field(
        ..., description="3 actionable improvement ideas"
    )
    total_reviews_analysed: int = Field(..., description="Total reviews in the corpus")
    week_label: str = Field(..., description="Week label e.g. 'Week of 10 Mar 2026'")
    raw_markdown: str = Field(
        default="", description="Full Markdown output from Gemini"
    )

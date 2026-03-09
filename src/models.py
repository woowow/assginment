from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class SourceQuote(BaseModel):
    file_name: str
    quote: str
    page: Optional[int] = None


class DailyItem(BaseModel):
    region: str
    headline: str
    bullet: str
    topic_key: str
    topic_label: str
    impact_hint: str = ""
    source_quotes: List[SourceQuote] = Field(default_factory=list)


class DailySummary(BaseModel):
    file_name: str
    file_date: str
    document_summary: str
    items: List[DailyItem] = Field(default_factory=list)


class WeeklyTopic(BaseModel):
    topic_key: str
    topic_label: str
    region: str
    latest_file_date: str
    latest_file_name: str
    latest_headline: str
    latest_bullet: str
    impact_hint: str = ""
    source_quotes: List[SourceQuote] = Field(default_factory=list)
    history: List[dict] = Field(default_factory=list)

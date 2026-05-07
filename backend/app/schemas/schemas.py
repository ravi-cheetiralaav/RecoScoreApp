"""Pydantic schemas for API serialization."""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


# ── SourcePost ─────────────────────────────────────────────────────────────

class SourcePostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str
    source: str
    raw_text: str
    post_url: Optional[str]
    posted_at: datetime
    ingested_at: datetime
    is_processed: bool


# ── Recommendation ──────────────────────────────────────────────────────────

class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_post_id: int
    raw_ticker: str
    resolved_ticker: Optional[str]
    exchange: str
    action: str
    mention_price: Optional[float]
    target_price: Optional[float]
    horizon_value: Optional[int]
    horizon_unit: Optional[str]
    confidence: float
    extraction_method: str
    entry_date: date
    is_active: bool
    notes: Optional[str]
    created_at: datetime


# ── Score ───────────────────────────────────────────────────────────────────

class RecommendationScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recommendation_id: int
    window_days: int
    entry_price: Optional[float]
    exit_price: Optional[float]
    return_pct: Optional[float]
    classification: str
    is_horizon_matched: bool
    computed_at: datetime


# ── Recommendation Detail ────────────────────────────────────────────────────

class RecommendationDetail(BaseModel):
    recommendation: RecommendationOut
    scores: List[RecommendationScoreOut]
    source_post: Optional[SourcePostOut]


# ── Summary Metrics ──────────────────────────────────────────────────────────

class SummaryMetrics(BaseModel):
    total_recommendations: int
    good: int
    bad: int
    neutral: int
    pending: int
    hit_rate: float
    avg_return_pct: float
    window_days: int


# ── Ingestion ────────────────────────────────────────────────────────────────

class IngestionTriggerRequest(BaseModel):
    limit: int = 50
    adapter: Optional[str] = None  # override adapter


class IngestionTriggerResponse(BaseModel):
    fetched: int
    new: int
    skipped: int
    processed: int  # recommendations extracted
    scored: int


# ── Filters ──────────────────────────────────────────────────────────────────

class RecommendationFilter(BaseModel):
    ticker: Optional[str] = None
    action: Optional[str] = None
    horizon_unit: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    classification: Optional[str] = None
    window_days: int = 90
    page: int = 1
    page_size: int = 20


class PaginatedRecommendations(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[RecommendationOut]

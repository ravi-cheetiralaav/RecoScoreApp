"""Recommendations API endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.recommendation import Recommendation
from app.models.recommendation_score import RecommendationScore
from app.models.source_post import SourcePost
from app.schemas.schemas import (
    RecommendationOut, RecommendationDetail, PaginatedRecommendations,
    RecommendationScoreOut, SourcePostOut
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=PaginatedRecommendations)
def list_recommendations(
    ticker: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    horizon_unit: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    classification: Optional[str] = Query(None),
    window_days: int = Query(90),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List recommendations with optional filters and pagination."""
    from datetime import date as date_type
    query = db.query(Recommendation).filter(Recommendation.is_active.is_(True))

    if ticker:
        t = ticker.upper()
        query = query.filter(
            (Recommendation.resolved_ticker.ilike(f"%{t}%")) |
            (Recommendation.raw_ticker.ilike(f"%{t}%"))
        )
    if action:
        query = query.filter(Recommendation.action == action.lower())
    if horizon_unit:
        query = query.filter(Recommendation.horizon_unit == horizon_unit.lower())
    if date_from:
        from datetime import datetime
        query = query.filter(Recommendation.entry_date >= datetime.strptime(date_from, "%Y-%m-%d").date())
    if date_to:
        from datetime import datetime
        query = query.filter(Recommendation.entry_date <= datetime.strptime(date_to, "%Y-%m-%d").date())

    # Filter by classification via join
    if classification:
        query = query.join(
            RecommendationScore,
            (RecommendationScore.recommendation_id == Recommendation.id) &
            (RecommendationScore.window_days == window_days)
        ).filter(RecommendationScore.classification == classification.lower())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedRecommendations(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


@router.get("/{rec_id}", response_model=RecommendationDetail)
def get_recommendation_detail(rec_id: int, db: Session = Depends(get_db)):
    """Get full details for a recommendation including all scores."""
    rec = db.query(Recommendation).filter(Recommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    scores = (
        db.query(RecommendationScore)
        .filter(RecommendationScore.recommendation_id == rec_id)
        .order_by(RecommendationScore.window_days)
        .all()
    )

    source_post = db.query(SourcePost).filter(SourcePost.id == rec.source_post_id).first()

    return RecommendationDetail(
        recommendation=rec,
        scores=scores,
        source_post=source_post,
    )

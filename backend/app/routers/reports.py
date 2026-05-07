"""Reports API endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.agents.report_agent import ReportAgent

router = APIRouter(prefix="/reports", tags=["reports"])

DISCLAIMER = (
    "DISCLAIMER: This analysis is for educational purposes only. "
    "It does not constitute investment advice. Past performance does not guarantee future results."
)


@router.get("/summary")
def get_summary(window_days: int = Query(90), db: Session = Depends(get_db)):
    """Get overall summary metrics."""
    agent = ReportAgent(db=db)
    return {**agent.summary_metrics(window_days), "disclaimer": DISCLAIMER}


@router.get("/hit-rate-by-month")
def get_hit_rate_by_month(window_days: int = Query(90), db: Session = Depends(get_db)):
    """Get hit rate grouped by month."""
    agent = ReportAgent(db=db)
    return {"data": agent.hit_rate_by_month(window_days), "disclaimer": DISCLAIMER}


@router.get("/top")
def get_top_recommendations(
    limit: int = Query(5),
    window_days: int = Query(90),
    db: Session = Depends(get_db),
):
    """Get top performing recommendations."""
    agent = ReportAgent(db=db)
    return {"data": agent.top_recommendations(limit=limit, window_days=window_days), "disclaimer": DISCLAIMER}


@router.get("/worst")
def get_worst_recommendations(
    limit: int = Query(5),
    window_days: int = Query(90),
    db: Session = Depends(get_db),
):
    """Get worst performing recommendations."""
    agent = ReportAgent(db=db)
    return {"data": agent.worst_recommendations(limit=limit, window_days=window_days), "disclaimer": DISCLAIMER}


@router.get("/full")
def get_full_report(window_days: int = Query(90), db: Session = Depends(get_db)):
    """Get full report including all metrics."""
    agent = ReportAgent(db=db)
    return agent.generate_report(window_days=window_days)

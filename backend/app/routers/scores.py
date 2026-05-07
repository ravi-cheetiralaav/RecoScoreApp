"""Scores API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.agents.scoring_agent import ScoringAgent
from app.agents.market_data_agent import MarketDataAgent
from app.models.recommendation import Recommendation
from app.config import get_settings

router = APIRouter(prefix="/scores", tags=["scores"])


@router.post("/recompute")
def recompute_scores(db: Session = Depends(get_db)):
    """Recompute all recommendation scores (market data + scoring)."""
    settings = get_settings()
    use_mock = settings.market_data_provider == "mock"

    recs = db.query(Recommendation).filter(Recommendation.is_active.is_(True)).all()

    market_agent = MarketDataAgent(db=db, use_mock=use_mock)
    market_agent.run(recs)

    scoring_agent = ScoringAgent(db=db)
    result = scoring_agent.run(recs)

    return {"message": "Scores recomputed", "total": result["total"], "scored": result["scored"]}

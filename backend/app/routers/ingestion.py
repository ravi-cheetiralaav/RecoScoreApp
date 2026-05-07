"""Ingestion API endpoints."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.agents.ingestion_agent import IngestionAgent, get_adapter
from app.agents.extraction_agent import ExtractionAgent
from app.agents.entity_resolution_agent import EntityResolutionAgent, seed_alias_table
from app.agents.market_data_agent import MarketDataAgent
from app.agents.scoring_agent import ScoringAgent
from app.models.source_post import SourcePost
from app.schemas.schemas import IngestionTriggerRequest, IngestionTriggerResponse
from app.config import get_settings

router = APIRouter(prefix="/ingestion", tags=["ingestion"])
logger = logging.getLogger(__name__)


@router.post("/trigger", response_model=IngestionTriggerResponse)
async def trigger_ingestion(
    request: IngestionTriggerRequest,
    db: Session = Depends(get_db),
):
    """
    Trigger the full ingestion pipeline:
    1. Ingest posts from adapter
    2. Extract recommendations
    3. Resolve entity tickers
    4. Fetch market data
    5. Compute scores
    """
    settings = get_settings()

    # Seed alias table if empty
    seed_alias_table(db)

    # Step 1: Ingest
    adapter = get_adapter(settings)
    agent = IngestionAgent(db=db, adapter=adapter)
    ingest_result = await agent.run(limit=request.limit)

    # Step 2: Extract from unprocessed posts
    unprocessed = (
        db.query(SourcePost)
        .filter(SourcePost.is_processed.is_(False))
        .all()
    )
    extraction_agent = ExtractionAgent(db=db)
    all_recs = []
    for post in unprocessed:
        recs = await extraction_agent.run(post)
        all_recs.extend(recs)

    # Step 3: Entity resolution
    entity_agent = EntityResolutionAgent(db=db)
    entity_agent.run(all_recs)

    # Step 4: Market data
    use_mock = settings.market_data_provider == "mock"
    market_agent = MarketDataAgent(db=db, use_mock=use_mock)
    market_agent.run(all_recs)

    # Step 5: Scoring
    scoring_agent = ScoringAgent(db=db)
    score_result = scoring_agent.run(all_recs)

    return IngestionTriggerResponse(
        fetched=ingest_result["fetched"],
        new=ingest_result["new"],
        skipped=ingest_result["skipped"],
        processed=len(all_recs),
        scored=score_result["scored"],
    )


@router.post("/reprocess")
async def reprocess_all(db: Session = Depends(get_db)):
    """Re-run market data fetch and scoring for all existing recommendations."""
    from app.models.recommendation import Recommendation

    seed_alias_table(db)
    settings = get_settings()
    use_mock = settings.market_data_provider == "mock"

    recs = db.query(Recommendation).filter(Recommendation.is_active.is_(True)).all()

    market_agent = MarketDataAgent(db=db, use_mock=use_mock)
    market_agent.run(recs)

    scoring_agent = ScoringAgent(db=db)
    result = scoring_agent.run(recs)

    return {"message": "Reprocessed", "total": result["total"], "scored": result["scored"]}

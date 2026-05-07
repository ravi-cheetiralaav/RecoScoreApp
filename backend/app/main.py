"""RecoScoreApp - FastAPI backend application.

Agentic stock recommendation analyzer.
DISCLAIMER: Educational analytics only, not investment advice.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from app.config import get_settings
from app.database import init_db, SessionLocal
from app.routers import ingestion, recommendations, scores, reports
from app.agents.entity_resolution_agent import seed_alias_table

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

scheduler = BackgroundScheduler()


def scheduled_recompute():
    """Periodic job: recompute scores for all recommendations."""
    from app.agents.market_data_agent import MarketDataAgent
    from app.agents.scoring_agent import ScoringAgent
    from app.models.recommendation import Recommendation

    logger.info("Scheduled recompute: starting")
    db = SessionLocal()
    try:
        recs = db.query(Recommendation).filter(Recommendation.is_active.is_(True)).all()
        use_mock = settings.market_data_provider == "mock"
        MarketDataAgent(db=db, use_mock=use_mock).run(recs)
        ScoringAgent(db=db).run(recs)
        logger.info("Scheduled recompute: done")
    except Exception as e:
        logger.error(f"Scheduled recompute failed: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting RecoScoreApp...")
    init_db()
    db = SessionLocal()
    seed_alias_table(db)
    db.close()

    scheduler.add_job(
        scheduled_recompute,
        "interval",
        hours=settings.score_recompute_interval_hours,
        id="recompute_scores",
    )
    scheduler.start()
    logger.info("Scheduler started")

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("RecoScoreApp stopped")


app = FastAPI(
    title="RecoScoreApp",
    description=(
        "Agentic stock recommendation analyzer. "
        "DISCLAIMER: For educational analytics only, not investment advice."
    ),
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion.router)
app.include_router(recommendations.router)
app.include_router(scores.router)
app.include_router(reports.router)


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "disclaimer": "Educational analytics only, not investment advice.",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}

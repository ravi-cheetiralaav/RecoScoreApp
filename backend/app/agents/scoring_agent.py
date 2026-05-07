"""Scoring Agent - computes recommendation outcomes across evaluation windows."""
import logging
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.recommendation import Recommendation
from app.models.price_snapshot import PriceSnapshot
from app.models.recommendation_score import RecommendationScore

logger = logging.getLogger(__name__)

settings = get_settings()

EVAL_WINDOWS = [30, 90, 180, 365]


def compute_return(action: str, entry_price: float, exit_price: float) -> float:
    """
    Compute return percentage based on action type.

    Buy/Hold: R = (exit - entry) / entry
    Sell/Avoid: R = (entry - exit) / entry  (profit if price fell)
    """
    if entry_price == 0:
        return 0.0
    if action in ("buy", "hold"):
        return (exit_price - entry_price) / entry_price
    else:  # sell, avoid
        return (entry_price - exit_price) / entry_price


def classify_return(return_pct: float, good_threshold: float = 0.05, bad_threshold: float = -0.05) -> str:
    """Classify a return as good / bad / neutral."""
    if return_pct > good_threshold:
        return "good"
    elif return_pct < bad_threshold:
        return "bad"
    return "neutral"


def _get_horizon_days(rec: Recommendation) -> Optional[int]:
    """Convert horizon to days for horizon-aware scoring."""
    if rec.horizon_value is None or rec.horizon_unit is None:
        return None
    unit = rec.horizon_unit.lower()
    mapping = {"day": 1, "week": 7, "month": 30, "year": 365}
    factor = mapping.get(unit, 30)
    return rec.horizon_value * factor


class ScoringAgent:
    """
    Scoring Agent.
    Computes recommendation outcomes at 30d, 90d, 180d, 365d windows.
    Implements the scoring formulas from requirements.
    """

    def __init__(self, db: Session):
        self.db = db
        self.good_threshold = settings.good_threshold
        self.bad_threshold = settings.bad_threshold

    def _get_snapshot_price(self, rec_id: int, snapshot_type: str) -> Optional[float]:
        snap = (
            self.db.query(PriceSnapshot)
            .filter(
                PriceSnapshot.recommendation_id == rec_id,
                PriceSnapshot.snapshot_type == snapshot_type,
            )
            .first()
        )
        return snap.close_price if snap else None

    def score_recommendation(self, rec: Recommendation) -> list[RecommendationScore]:
        """Compute scores for a single recommendation across all windows."""
        entry_price = self._get_snapshot_price(rec.id, "entry")
        if entry_price is None:
            # Use mention_price as fallback
            entry_price = rec.mention_price

        if entry_price is None:
            logger.debug(f"No entry price for rec {rec.id}, skipping")
            return []

        horizon_days = _get_horizon_days(rec)
        saved_scores = []

        for window_days in EVAL_WINDOWS:
            snap_key = f"d{window_days}"
            exit_price = self._get_snapshot_price(rec.id, snap_key)

            if exit_price is None:
                # Check if date has passed
                eval_date = rec.entry_date + timedelta(days=window_days)
                if eval_date > date.today():
                    classification = "pending"
                    return_pct = None
                else:
                    classification = "pending"
                    return_pct = None
            else:
                return_pct = compute_return(rec.action, entry_price, exit_price)
                classification = classify_return(
                    return_pct,
                    good_threshold=self.good_threshold,
                    bad_threshold=self.bad_threshold,
                )

            is_horizon_matched = horizon_days is not None and abs(window_days - horizon_days) <= 15

            # Upsert score record
            existing = (
                self.db.query(RecommendationScore)
                .filter(
                    RecommendationScore.recommendation_id == rec.id,
                    RecommendationScore.window_days == window_days,
                )
                .first()
            )

            if existing:
                existing.entry_price = entry_price
                existing.exit_price = exit_price
                existing.return_pct = return_pct
                existing.classification = classification
                existing.is_horizon_matched = is_horizon_matched
                from datetime import datetime
                existing.computed_at = datetime.utcnow()
                saved_scores.append(existing)
            else:
                score = RecommendationScore(
                    recommendation_id=rec.id,
                    window_days=window_days,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    return_pct=return_pct,
                    classification=classification,
                    is_horizon_matched=is_horizon_matched,
                )
                self.db.add(score)
                saved_scores.append(score)

        self.db.commit()
        return saved_scores

    def run(self, recommendations: list[Recommendation]) -> dict:
        """Score all recommendations. Returns summary dict."""
        total = 0
        scored = 0
        for rec in recommendations:
            scores = self.score_recommendation(rec)
            total += 1
            if scores:
                scored += 1
        logger.info(f"ScoringAgent: scored {scored}/{total} recommendations")
        return {"total": total, "scored": scored}

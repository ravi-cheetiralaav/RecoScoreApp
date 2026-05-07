"""Report Agent - generates summary reports from scored recommendations."""
import logging
from collections import defaultdict
from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.recommendation import Recommendation
from app.models.recommendation_score import RecommendationScore

logger = logging.getLogger(__name__)


class ReportAgent:
    """
    Report Agent.
    Generates hit rate, average return, best/worst calls, and trend summaries.
    """

    def __init__(self, db: Session):
        self.db = db

    def _base_query(self, window_days: int = 90):
        return (
            self.db.query(RecommendationScore, Recommendation)
            .join(Recommendation, RecommendationScore.recommendation_id == Recommendation.id)
            .filter(RecommendationScore.window_days == window_days)
        )

    def summary_metrics(self, window_days: int = 90) -> dict:
        """Return overall summary metrics."""
        total_recs = self.db.query(Recommendation).filter(Recommendation.is_active.is_(True)).count()

        scores = (
            self.db.query(RecommendationScore)
            .filter(RecommendationScore.window_days == window_days)
            .all()
        )

        counts = defaultdict(int)
        returns = []
        for s in scores:
            counts[s.classification] += 1
            if s.return_pct is not None:
                returns.append(s.return_pct)

        good = counts.get("good", 0)
        bad = counts.get("bad", 0)
        neutral = counts.get("neutral", 0)
        pending = counts.get("pending", 0)
        total_scored = good + bad + neutral

        hit_rate = good / total_scored if total_scored > 0 else 0.0
        avg_return = sum(returns) / len(returns) if returns else 0.0

        return {
            "total_recommendations": total_recs,
            "good": good,
            "bad": bad,
            "neutral": neutral,
            "pending": pending,
            "hit_rate": round(hit_rate, 4),
            "avg_return_pct": round(avg_return * 100, 2),
            "window_days": window_days,
        }

    def hit_rate_by_month(self, window_days: int = 90) -> list[dict]:
        """Return hit rate grouped by entry month."""
        rows = self._base_query(window_days).all()

        monthly = defaultdict(lambda: {"good": 0, "bad": 0, "neutral": 0, "total": 0})
        for score, rec in rows:
            if score.classification == "pending":
                continue
            month_key = rec.entry_date.strftime("%Y-%m")
            monthly[month_key][score.classification] += 1
            monthly[month_key]["total"] += 1

        result = []
        for month, counts in sorted(monthly.items()):
            total = counts["total"]
            hit_rate = counts["good"] / total if total > 0 else 0.0
            result.append({
                "month": month,
                "good": counts["good"],
                "bad": counts["bad"],
                "neutral": counts["neutral"],
                "total": total,
                "hit_rate": round(hit_rate, 4),
            })
        return result

    def top_recommendations(self, limit: int = 5, window_days: int = 90) -> list[dict]:
        """Return top performing recommendations by return_pct."""
        rows = (
            self._base_query(window_days)
            .filter(RecommendationScore.return_pct.isnot(None))
            .order_by(RecommendationScore.return_pct.desc())
            .limit(limit)
            .all()
        )
        return self._format_rows(rows)

    def worst_recommendations(self, limit: int = 5, window_days: int = 90) -> list[dict]:
        """Return worst performing recommendations by return_pct."""
        rows = (
            self._base_query(window_days)
            .filter(RecommendationScore.return_pct.isnot(None))
            .order_by(RecommendationScore.return_pct.asc())
            .limit(limit)
            .all()
        )
        return self._format_rows(rows)

    def _format_rows(self, rows: list) -> list[dict]:
        result = []
        for score, rec in rows:
            result.append({
                "recommendation_id": rec.id,
                "ticker": rec.resolved_ticker or rec.raw_ticker,
                "action": rec.action,
                "entry_date": rec.entry_date.isoformat(),
                "mention_price": rec.mention_price,
                "target_price": rec.target_price,
                "entry_price": score.entry_price,
                "exit_price": score.exit_price,
                "return_pct": round(score.return_pct * 100, 2) if score.return_pct else None,
                "classification": score.classification,
                "window_days": score.window_days,
            })
        return result

    def generate_report(self, window_days: int = 90) -> dict:
        """Generate a full report."""
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "window_days": window_days,
            "summary": self.summary_metrics(window_days),
            "hit_rate_by_month": self.hit_rate_by_month(window_days),
            "top_recommendations": self.top_recommendations(window_days=window_days),
            "worst_recommendations": self.worst_recommendations(window_days=window_days),
            "disclaimer": (
                "DISCLAIMER: This analysis is for educational purposes only. "
                "It does not constitute investment advice. Past performance "
                "does not guarantee future results."
            ),
        }

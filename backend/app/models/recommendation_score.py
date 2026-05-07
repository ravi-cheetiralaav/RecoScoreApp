"""RecommendationScore model - computed scores for recommendations."""
from datetime import datetime
from sqlalchemy import String, Float, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ScoreClassification(str):
    GOOD = "good"
    BAD = "bad"
    NEUTRAL = "neutral"
    PENDING = "pending"


class RecommendationScore(Base):
    __tablename__ = "recommendation_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recommendation_id: Mapped[int] = mapped_column(Integer, ForeignKey("recommendations.id"), index=True)

    # Window: 30 | 90 | 180 | 365
    window_days: Mapped[int] = mapped_column(Integer, index=True)

    entry_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    return_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    # good | bad | neutral | pending
    classification: Mapped[str] = mapped_column(String(20), default="pending")

    is_horizon_matched: Mapped[bool] = mapped_column(Boolean, default=False)

    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    recommendation = relationship("Recommendation", back_populates="scores")

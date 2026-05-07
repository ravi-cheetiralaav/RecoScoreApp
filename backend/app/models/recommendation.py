"""Recommendation model - extracted recommendations from posts."""
from datetime import datetime, date
from sqlalchemy import String, Float, Integer, ForeignKey, DateTime, Date, Enum, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.database import Base


class ActionType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    AVOID = "avoid"


class HorizonUnit(str, enum.Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_post_id: Mapped[int] = mapped_column(Integer, ForeignKey("source_posts.id"), index=True)

    # Core fields
    raw_ticker: Mapped[str] = mapped_column(String(50))  # as mentioned in post
    resolved_ticker: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    exchange: Mapped[str] = mapped_column(String(10), default="NSE")  # NSE | BSE

    action: Mapped[str] = mapped_column(String(10))  # buy | sell | hold | avoid
    mention_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Horizon
    horizon_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    horizon_unit: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Confidence
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    extraction_method: Mapped[str] = mapped_column(String(20), default="rule")  # rule | llm

    # Dates
    entry_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    source_post = relationship("SourcePost", back_populates="recommendations")
    scores = relationship("RecommendationScore", back_populates="recommendation")
    price_snapshots = relationship("PriceSnapshot", back_populates="recommendation")

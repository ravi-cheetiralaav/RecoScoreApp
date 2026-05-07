"""PriceSnapshot model - price data points for recommendations."""
from datetime import datetime, date
from sqlalchemy import String, Float, Integer, ForeignKey, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recommendation_id: Mapped[int] = mapped_column(Integer, ForeignKey("recommendations.id"), index=True)
    ticker: Mapped[str] = mapped_column(String(50), index=True)
    price_date: Mapped[date] = mapped_column(Date, index=True)
    close_price: Mapped[float] = mapped_column(Float)
    snapshot_type: Mapped[str] = mapped_column(String(20))  # entry | d30 | d90 | d180 | d365 | current
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    provider: Mapped[str] = mapped_column(String(20), default="yfinance")

    # Relationships
    recommendation = relationship("Recommendation", back_populates="price_snapshots")

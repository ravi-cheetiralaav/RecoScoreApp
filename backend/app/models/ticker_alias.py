"""TickerAlias model - maps company names/aliases to NSE/BSE tickers."""
from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class TickerAlias(Base):
    __tablename__ = "ticker_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    alias: Mapped[str] = mapped_column(String(100), index=True)  # e.g. "reliance", "RIL"
    ticker: Mapped[str] = mapped_column(String(50), index=True)  # e.g. "RELIANCE"
    exchange: Mapped[str] = mapped_column(String(10), default="NSE")
    yfinance_symbol: Mapped[str] = mapped_column(String(50))  # e.g. "RELIANCE.NS"
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

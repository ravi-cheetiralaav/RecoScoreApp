"""Market Data Agent - fetches price snapshots for recommendations."""
import logging
from datetime import date, datetime, timedelta
from typing import Optional

import yfinance as yf
from sqlalchemy.orm import Session

from app.models.recommendation import Recommendation
from app.models.price_snapshot import PriceSnapshot

logger = logging.getLogger(__name__)

SNAPSHOT_TYPES = {
    "entry": 0,
    "d30": 30,
    "d90": 90,
    "d180": 180,
    "d365": 365,
}


def _get_price_on_date(symbol: str, target_date: date) -> Optional[float]:
    """Fetch closing price for a symbol on or near a target_date using yfinance."""
    try:
        # Fetch a small window around the target date to handle weekends/holidays
        start = target_date - timedelta(days=5)
        end = target_date + timedelta(days=5)

        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start.isoformat(), end=end.isoformat())

        if hist.empty:
            return None

        # Find the closest date <= target_date
        hist.index = hist.index.normalize()
        target_ts = datetime.combine(target_date, datetime.min.time())
        past_dates = hist[hist.index <= target_ts]

        if past_dates.empty:
            # Use first available
            return float(hist["Close"].iloc[0])

        return float(past_dates["Close"].iloc[-1])
    except Exception as e:
        logger.error(f"Error fetching price for {symbol} on {target_date}: {e}")
        return None


def _get_mock_price(symbol: str, target_date: date) -> float:
    """Return a deterministic mock price for testing."""
    import hashlib
    seed = int(hashlib.md5(f"{symbol}{target_date}".encode()).hexdigest()[:8], 16)
    base_prices = {
        "RELIANCE.NS": 2400, "TCS.NS": 3800, "INFY.NS": 1450,
        "HDFCBANK.NS": 1700, "TATAMOTORS.NS": 780, "WIPRO.NS": 480,
        "SUNPHARMA.NS": 1600, "BAJFINANCE.NS": 7200, "ITC.NS": 450,
        "MARUTI.NS": 11500, "ONGC.NS": 255, "COALINDIA.NS": 470,
        "HINDUNILVR.NS": 2300, "ZOMATO.NS": 220, "SBIN.NS": 760,
        "HCLTECH.NS": 1550, "POWERGRID.NS": 290, "ADANIENT.NS": 2500,
        "YESBANK.NS": 18, "AXISBANK.NS": 1100,
    }
    base = base_prices.get(symbol, 1000)
    # Simulate ~5-15% variation over time
    variation = (seed % 200 - 100) / 1000.0
    return round(base * (1 + variation), 2)


class MarketDataAgent:
    """
    Market Data Agent.
    Fetches price snapshots at entry date and evaluation windows (30d, 90d, 180d, 365d).
    """

    def __init__(self, db: Session, use_mock: bool = False):
        self.db = db
        self.use_mock = use_mock

    def _get_price(self, symbol: str, target_date: date) -> Optional[float]:
        if self.use_mock:
            return _get_mock_price(symbol, target_date)
        return _get_price_on_date(symbol, target_date)

    def _save_snapshot(
        self,
        rec: Recommendation,
        snapshot_type: str,
        price_date: date,
        price: float,
    ) -> PriceSnapshot:
        """Save or update a price snapshot."""
        existing = (
            self.db.query(PriceSnapshot)
            .filter(
                PriceSnapshot.recommendation_id == rec.id,
                PriceSnapshot.snapshot_type == snapshot_type,
            )
            .first()
        )
        if existing:
            existing.close_price = price
            existing.price_date = price_date
            existing.fetched_at = datetime.utcnow()
            existing.provider = "mock" if self.use_mock else "yfinance"
            return existing

        snap = PriceSnapshot(
            recommendation_id=rec.id,
            ticker=rec.resolved_ticker or rec.raw_ticker,
            price_date=price_date,
            close_price=price,
            snapshot_type=snapshot_type,
            provider="mock" if self.use_mock else "yfinance",
        )
        self.db.add(snap)
        return snap

    def fetch_snapshots_for_recommendation(self, rec: Recommendation) -> dict:
        """Fetch all required price snapshots for a recommendation."""
        symbol = rec.resolved_ticker or rec.raw_ticker
        if not symbol:
            logger.warning(f"No ticker symbol for recommendation {rec.id}")
            return {}

        today = date.today()
        entry_date = rec.entry_date
        fetched = {}

        for snap_type, offset_days in SNAPSHOT_TYPES.items():
            target_date = entry_date + timedelta(days=offset_days)
            if target_date > today:
                continue  # future date, skip

            price = self._get_price(symbol, target_date)
            if price is not None:
                self._save_snapshot(rec, snap_type, target_date, price)
                fetched[snap_type] = price

        self.db.commit()
        logger.debug(f"MarketDataAgent: fetched {len(fetched)} snapshots for rec {rec.id}")
        return fetched

    def run(self, recommendations: list[Recommendation]) -> int:
        """Fetch snapshots for all recommendations. Returns count processed."""
        count = 0
        for rec in recommendations:
            if not rec.resolved_ticker:
                continue
            self.fetch_snapshots_for_recommendation(rec)
            count += 1
        logger.info(f"MarketDataAgent: processed {count} recommendations")
        return count

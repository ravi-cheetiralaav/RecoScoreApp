"""Entity Resolution Agent - maps raw ticker names to canonical NSE/BSE tickers."""
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.ticker_alias import TickerAlias
from app.models.recommendation import Recommendation

logger = logging.getLogger(__name__)

# Built-in alias table for common NSE stocks
BUILTIN_ALIASES = [
    # (alias, ticker, exchange, yfinance_symbol)
    ("RELIANCE", "RELIANCE", "NSE", "RELIANCE.NS"),
    ("RIL", "RELIANCE", "NSE", "RELIANCE.NS"),
    ("TCS", "TCS", "NSE", "TCS.NS"),
    ("INFY", "INFY", "NSE", "INFY.NS"),
    ("INFOSYS", "INFY", "NSE", "INFY.NS"),
    ("HDFCBANK", "HDFCBANK", "NSE", "HDFCBANK.NS"),
    ("HDFC", "HDFCBANK", "NSE", "HDFCBANK.NS"),
    ("HDFC BANK", "HDFCBANK", "NSE", "HDFCBANK.NS"),
    ("ICICIBANK", "ICICIBANK", "NSE", "ICICIBANK.NS"),
    ("ICICI", "ICICIBANK", "NSE", "ICICIBANK.NS"),
    ("SBIN", "SBIN", "NSE", "SBIN.NS"),
    ("SBI", "SBIN", "NSE", "SBIN.NS"),
    ("WIPRO", "WIPRO", "NSE", "WIPRO.NS"),
    ("HCLTECH", "HCLTECH", "NSE", "HCLTECH.NS"),
    ("HCL", "HCLTECH", "NSE", "HCLTECH.NS"),
    ("TATAMOTORS", "TATAMOTORS", "NSE", "TATAMOTORS.NS"),
    ("TATA MOTORS", "TATAMOTORS", "NSE", "TATAMOTORS.NS"),
    ("SUNPHARMA", "SUNPHARMA", "NSE", "SUNPHARMA.NS"),
    ("SUN PHARMA", "SUNPHARMA", "NSE", "SUNPHARMA.NS"),
    ("BAJFINANCE", "BAJFINANCE", "NSE", "BAJFINANCE.NS"),
    ("BAJ FINANCE", "BAJFINANCE", "NSE", "BAJFINANCE.NS"),
    ("BAJAJ FINANCE", "BAJFINANCE", "NSE", "BAJFINANCE.NS"),
    ("ITC", "ITC", "NSE", "ITC.NS"),
    ("MARUTI", "MARUTI", "NSE", "MARUTI.NS"),
    ("ONGC", "ONGC", "NSE", "ONGC.NS"),
    ("COALINDIA", "COALINDIA", "NSE", "COALINDIA.NS"),
    ("COAL INDIA", "COALINDIA", "NSE", "COALINDIA.NS"),
    ("HUL", "HINDUNILVR", "NSE", "HINDUNILVR.NS"),
    ("HINDUNILVR", "HINDUNILVR", "NSE", "HINDUNILVR.NS"),
    ("HINDUSTAN UNILEVER", "HINDUNILVR", "NSE", "HINDUNILVR.NS"),
    ("ZOMATO", "ZOMATO", "NSE", "ZOMATO.NS"),
    ("ADANIENT", "ADANIENT", "NSE", "ADANIENT.NS"),
    ("ADANI", "ADANIENT", "NSE", "ADANIENT.NS"),
    ("POWERGRID", "POWERGRID", "NSE", "POWERGRID.NS"),
    ("POWER GRID", "POWERGRID", "NSE", "POWERGRID.NS"),
    ("YESBANK", "YESBANK", "NSE", "YESBANK.NS"),
    ("YES BANK", "YESBANK", "NSE", "YESBANK.NS"),
    ("NIFTY50", "NIFTY50", "NSE", "^NSEI"),
    ("NIFTY", "NIFTY50", "NSE", "^NSEI"),
    ("AXISBANK", "AXISBANK", "NSE", "AXISBANK.NS"),
    ("AXIS BANK", "AXISBANK", "NSE", "AXISBANK.NS"),
    ("KOTAKBANK", "KOTAKBANK", "NSE", "KOTAKBANK.NS"),
    ("KOTAK", "KOTAKBANK", "NSE", "KOTAKBANK.NS"),
    ("LTIM", "LTIM", "NSE", "LTIM.NS"),
    ("LT", "LT", "NSE", "LT.NS"),
    ("TECHM", "TECHM", "NSE", "TECHM.NS"),
    ("TITAN", "TITAN", "NSE", "TITAN.NS"),
    ("ULTRACEMCO", "ULTRACEMCO", "NSE", "ULTRACEMCO.NS"),
    ("NESTLEIND", "NESTLEIND", "NSE", "NESTLEIND.NS"),
    ("NESTLE", "NESTLEIND", "NSE", "NESTLEIND.NS"),
    ("BHARTIARTL", "BHARTIARTL", "NSE", "BHARTIARTL.NS"),
    ("AIRTEL", "BHARTIARTL", "NSE", "BHARTIARTL.NS"),
    ("DRREDDY", "DRREDDY", "NSE", "DRREDDY.NS"),
    ("CIPLA", "CIPLA", "NSE", "CIPLA.NS"),
    ("DIVISLAB", "DIVISLAB", "NSE", "DIVISLAB.NS"),
    ("ASIANPAINT", "ASIANPAINT", "NSE", "ASIANPAINT.NS"),
    ("ASIAN PAINTS", "ASIANPAINT", "NSE", "ASIANPAINT.NS"),
    ("PIDILITIND", "PIDILITIND", "NSE", "PIDILITIND.NS"),
    ("HAVELLS", "HAVELLS", "NSE", "HAVELLS.NS"),
    ("VOLTAS", "VOLTAS", "NSE", "VOLTAS.NS"),
]


def seed_alias_table(db: Session):
    """Seed the TickerAlias table with built-in aliases if empty."""
    if db.query(TickerAlias).count() == 0:
        for alias, ticker, exchange, yf_symbol in BUILTIN_ALIASES:
            db.add(
                TickerAlias(
                    alias=alias.upper(),
                    ticker=ticker,
                    exchange=exchange,
                    yfinance_symbol=yf_symbol,
                    confidence=1.0,
                )
            )
        db.commit()
        logger.info(f"Seeded {len(BUILTIN_ALIASES)} ticker aliases")


class EntityResolutionAgent:
    """
    Entity Resolution Agent.
    Maps raw_ticker (from extraction) to a canonical NSE/BSE ticker symbol.
    """

    def __init__(self, db: Session):
        self.db = db

    def resolve(self, raw_ticker: str) -> tuple[Optional[str], Optional[str], float]:
        """
        Resolve a raw ticker to (canonical_ticker, yfinance_symbol, confidence).
        Returns (None, None, 0.0) if unresolved.
        """
        key = raw_ticker.upper().strip()
        alias = (
            self.db.query(TickerAlias)
            .filter(TickerAlias.alias == key, TickerAlias.is_active.is_(True))
            .first()
        )
        if alias:
            return alias.ticker, alias.yfinance_symbol, alias.confidence

        # Fuzzy fallback: try if the raw_ticker IS a valid ticker itself
        # (e.g., RELIANCE.NS directly)
        if "." in raw_ticker:
            return raw_ticker, raw_ticker, 0.6

        # Partial match: alias starts with raw_ticker
        partial = (
            self.db.query(TickerAlias)
            .filter(
                TickerAlias.alias.startswith(key),
                TickerAlias.is_active.is_(True),
            )
            .first()
        )
        if partial:
            return partial.ticker, partial.yfinance_symbol, partial.confidence * 0.7

        return None, None, 0.0

    def run(self, recommendations: list[Recommendation]) -> int:
        """
        Resolve tickers for a list of recommendations.
        Returns count of successfully resolved.
        """
        resolved_count = 0
        for rec in recommendations:
            ticker, yf_symbol, conf = self.resolve(rec.raw_ticker)
            if ticker:
                rec.resolved_ticker = yf_symbol  # store yfinance symbol for easy lookup
                rec.confidence = min(rec.confidence, conf) if conf < 1.0 else rec.confidence
                resolved_count += 1
            else:
                logger.warning(f"Could not resolve ticker: {rec.raw_ticker}")

        self.db.commit()
        logger.info(f"EntityResolutionAgent: resolved {resolved_count}/{len(recommendations)}")
        return resolved_count

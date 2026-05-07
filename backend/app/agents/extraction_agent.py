"""Recommendation Extraction Agent.

Parses raw post text to extract:
- ticker symbol (raw)
- action: buy / sell / hold / avoid
- mention price (entry price mentioned in post)
- target price
- horizon (e.g., 3 months, 1 year)
- confidence score

Supports English and Hinglish text.
Uses rule-based extraction as primary method.
LLM-based extraction can be enabled via config.
"""
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.source_post import SourcePost
from app.models.recommendation import Recommendation
from app.models.extraction_audit import ExtractionAudit

logger = logging.getLogger(__name__)

PROMPT_VERSION = "v1.0"

# ── Rule-based patterns ──────────────────────────────────────────────────────

# Ticker: all-caps word 2-15 chars, optionally preceded by $ or #
TICKER_RE = re.compile(
    r"""(?:^|\s|\$|#)([A-Z][A-Z0-9&]{1,14})(?=\s|$|[^A-Z0-9])""",
    re.MULTILINE,
)

# Price: ₹ or Rs or INR followed by number
PRICE_RE = re.compile(
    r"""(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)""",
    re.IGNORECASE,
)

# Action keywords
BUY_RE = re.compile(r'\b(buy|long|accumulate|add|purchase|entry lo|kharid|bullish)\b', re.IGNORECASE)
SELL_RE = re.compile(r'\b(sell|short|exit|becho|bearish)\b', re.IGNORECASE)
HOLD_RE = re.compile(r'\b(hold|rakh|wait|maintain)\b', re.IGNORECASE)
AVOID_RE = re.compile(r'\b(avoid|skip|stay away|mat lo|risky|danger)\b', re.IGNORECASE)

# Horizon: e.g. "3 months", "1 year", "30 days", "6 mahine"
HORIZON_RE = re.compile(
    r"""(\d+)\s*(?:-\s*\d+\s*)?"""
    r"""(day|days|week|weeks|month|months|mahine|year|years|sal)\b""",
    re.IGNORECASE,
)

HORIZON_UNIT_MAP = {
    "day": "day", "days": "day",
    "week": "week", "weeks": "week",
    "month": "month", "months": "month", "mahine": "month",
    "year": "year", "years": "year", "sal": "year",
}

# Noise words to exclude from ticker detection
TICKER_STOP_WORDS = {
    "BUY", "SELL", "HOLD", "AVOID", "TARGET", "PRICE", "AT", "IN", "FOR",
    "THE", "THIS", "AND", "OR", "IS", "ARE", "BE", "INR", "RS", "PE",
    "KE", "KO", "MEIN", "HAI", "HO", "NIFTY", "SENSEX",
}


@dataclass
class ExtractedRecommendation:
    raw_ticker: str
    action: str
    mention_price: Optional[float]
    target_price: Optional[float]
    horizon_value: Optional[int]
    horizon_unit: Optional[str]
    confidence: float
    extraction_method: str = "rule"
    notes: str = ""


def _extract_prices(text: str) -> List[float]:
    """Return all prices mentioned in the text."""
    prices = []
    for m in PRICE_RE.finditer(text):
        try:
            prices.append(float(m.group(1).replace(",", "")))
        except ValueError:
            pass
    return prices


def _extract_action(text: str) -> tuple[str, float]:
    """Return (action, confidence) from text."""
    if AVOID_RE.search(text):
        return "avoid", 0.85
    if SELL_RE.search(text):
        return "sell", 0.85
    if HOLD_RE.search(text):
        return "hold", 0.75
    if BUY_RE.search(text):
        return "buy", 0.85
    return "buy", 0.4  # default / uncertain


def _extract_tickers(text: str) -> List[str]:
    """Return candidate tickers from text."""
    candidates = []
    for m in TICKER_RE.finditer(text):
        ticker = m.group(1).upper()
        if ticker not in TICKER_STOP_WORDS and len(ticker) >= 2:
            candidates.append(ticker)
    return list(dict.fromkeys(candidates))  # preserve order, deduplicate


def _extract_horizon(text: str) -> tuple[Optional[int], Optional[str]]:
    """Return (horizon_value, horizon_unit) from text."""
    m = HORIZON_RE.search(text)
    if m:
        value = int(m.group(1))
        unit = HORIZON_UNIT_MAP.get(m.group(2).lower())
        return value, unit
    return None, None


def rule_based_extract(text: str) -> List[ExtractedRecommendation]:
    """Apply rule-based extraction and return list of recommendations."""
    prices = _extract_prices(text)
    action, action_conf = _extract_action(text)
    tickers = _extract_tickers(text)
    horizon_value, horizon_unit = _extract_horizon(text)

    if not tickers:
        return []

    mention_price = prices[0] if prices else None
    target_price = prices[1] if len(prices) > 1 else None

    # If action is "target" keyword found, second price is target
    if "target" in text.lower() and len(prices) >= 2:
        # first price = entry, second price = target
        mention_price = prices[0]
        target_price = prices[1]

    confidence = action_conf
    if mention_price:
        confidence = min(confidence + 0.05, 1.0)
    if horizon_unit:
        confidence = min(confidence + 0.05, 1.0)

    results = []
    for ticker in tickers[:2]:  # max 2 tickers per post
        results.append(
            ExtractedRecommendation(
                raw_ticker=ticker,
                action=action,
                mention_price=mention_price,
                target_price=target_price,
                horizon_value=horizon_value,
                horizon_unit=horizon_unit,
                confidence=confidence,
                extraction_method="rule",
            )
        )
    return results


async def llm_extract(text: str, api_key: str) -> List[ExtractedRecommendation]:
    """Optional LLM-based extraction (requires OpenAI API key)."""
    try:
        import openai

        client = openai.AsyncOpenAI(api_key=api_key)
        prompt = f"""You are a financial analyst. Extract all stock recommendations from the following post.
Return a JSON array of objects with these fields:
- raw_ticker: string (ticker/company name as mentioned)
- action: "buy" | "sell" | "hold" | "avoid"
- mention_price: number or null (price mentioned for entry)
- target_price: number or null
- horizon_value: integer or null
- horizon_unit: "day" | "week" | "month" | "year" | null
- confidence: float 0-1

Post: {text}

Return ONLY the JSON array, nothing else."""

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=500,
        )
        raw_output = response.choices[0].message.content.strip()
        data = json.loads(raw_output)
        return [
            ExtractedRecommendation(
                raw_ticker=item.get("raw_ticker", "UNKNOWN"),
                action=item.get("action", "buy"),
                mention_price=item.get("mention_price"),
                target_price=item.get("target_price"),
                horizon_value=item.get("horizon_value"),
                horizon_unit=item.get("horizon_unit"),
                confidence=item.get("confidence", 0.7),
                extraction_method="llm",
            )
            for item in data
        ]
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        return []


class ExtractionAgent:
    """
    Recommendation Extraction Agent.
    Extracts structured recommendations from raw post text.
    """

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    async def run(self, source_post: SourcePost) -> List[Recommendation]:
        """Extract recommendations from a source post and persist them."""
        text = source_post.raw_text
        extracted = []
        method = "rule"
        raw_llm_output = None

        # Try LLM extraction if configured
        if self.settings.use_llm_extraction and self.settings.openai_api_key:
            try:
                extracted = await llm_extract(text, self.settings.openai_api_key)
                method = "llm"
                raw_llm_output = json.dumps([e.__dict__ for e in extracted])
            except Exception as e:
                logger.warning(f"LLM extraction failed, falling back to rule-based: {e}")

        # Fallback to rule-based
        if not extracted:
            extracted = rule_based_extract(text)
            method = "rule"

        # Record extraction audit
        audit = ExtractionAudit(
            source_post_id=source_post.id,
            extraction_method=method,
            prompt_version=PROMPT_VERSION if method == "llm" else None,
            raw_llm_output=raw_llm_output,
            normalized_output=json.dumps([e.__dict__ for e in extracted]),
            confidence=max((e.confidence for e in extracted), default=0.0),
        )
        self.db.add(audit)

        # Persist recommendations
        saved = []
        for ext in extracted:
            rec = Recommendation(
                source_post_id=source_post.id,
                raw_ticker=ext.raw_ticker,
                resolved_ticker=None,  # will be filled by EntityResolutionAgent
                action=ext.action,
                mention_price=ext.mention_price,
                target_price=ext.target_price,
                horizon_value=ext.horizon_value,
                horizon_unit=ext.horizon_unit,
                confidence=ext.confidence,
                extraction_method=ext.extraction_method,
                entry_date=source_post.posted_at.date(),
            )
            self.db.add(rec)
            saved.append(rec)

        # Mark post as processed
        source_post.is_processed = True
        self.db.commit()

        for rec in saved:
            self.db.refresh(rec)

        logger.info(
            f"ExtractionAgent: post={source_post.id}, extracted={len(saved)} recommendations"
        )
        return saved

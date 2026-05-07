"""Tests for rule-based extraction parser."""
import pytest
from app.agents.extraction_agent import (
    rule_based_extract,
    _extract_prices,
    _extract_action,
    _extract_tickers,
    _extract_horizon,
)


class TestExtractPrices:
    def test_rupee_symbol(self):
        prices = _extract_prices("Buy RELIANCE at ₹2400, target ₹2700")
        assert prices == [2400.0, 2700.0]

    def test_rs_prefix(self):
        prices = _extract_prices("entry Rs 150, target Rs.200")
        assert prices == [150.0, 200.0]

    def test_inr_prefix(self):
        prices = _extract_prices("Buy at INR 1450")
        assert prices == [1450.0]

    def test_no_price(self):
        prices = _extract_prices("Buy RELIANCE, strong fundamentals")
        assert prices == []

    def test_comma_in_price(self):
        prices = _extract_prices("Buy at ₹11,500")
        assert prices == [11500.0]


class TestExtractAction:
    def test_buy(self):
        action, conf = _extract_action("buy RELIANCE at 2400")
        assert action == "buy"
        assert conf > 0.5

    def test_sell(self):
        action, conf = _extract_action("sell HDFC now")
        assert action == "sell"

    def test_avoid(self):
        action, conf = _extract_action("Avoid YESBANK at current price")
        assert action == "avoid"

    def test_hold(self):
        action, conf = _extract_action("hold WIPRO, accumulate on dips")
        assert action == "hold"

    def test_hinglish_buy(self):
        action, conf = _extract_action("RELIANCE mein entry lo ₹2400 pe")
        assert action == "buy"

    def test_hinglish_avoid(self):
        action, conf = _extract_action("mat lo yesbank, risky hai")
        assert action == "avoid"


class TestExtractTickers:
    def test_simple_ticker(self):
        tickers = _extract_tickers("Buy RELIANCE at ₹2400")
        assert "RELIANCE" in tickers

    def test_multiple_tickers(self):
        tickers = _extract_tickers("Buy TCS and INFY for good returns")
        assert "TCS" in tickers
        assert "INFY" in tickers

    def test_noise_words_excluded(self):
        tickers = _extract_tickers("BUY RELIANCE AT ₹2400 TARGET ₹2700 IN 3 months")
        assert "BUY" not in tickers
        assert "AT" not in tickers
        assert "TARGET" not in tickers
        assert "RELIANCE" in tickers


class TestExtractHorizon:
    def test_months(self):
        val, unit = _extract_horizon("target ₹2700 in 3 months")
        assert val == 3
        assert unit == "month"

    def test_year(self):
        val, unit = _extract_horizon("1 year target ₹4500")
        assert val == 1
        assert unit == "year"

    def test_days(self):
        val, unit = _extract_horizon("target in 30 days")
        assert val == 30
        assert unit == "day"

    def test_hinglish_mahine(self):
        val, unit = _extract_horizon("6 mahine mein ₹950 dekh sakte hain")
        assert val == 6
        assert unit == "month"

    def test_no_horizon(self):
        val, unit = _extract_horizon("Strong buy at ₹2400")
        assert val is None
        assert unit is None


class TestRuleBasedExtract:
    def test_full_buy_post(self):
        text = "RELIANCE ₹2400 pe buy karo, target ₹2700, horizon 3 months. Strong fundamentals!"
        results = rule_based_extract(text)
        assert len(results) >= 1
        r = results[0]
        assert r.action == "buy"
        assert r.mention_price == 2400.0
        assert r.target_price == 2700.0
        assert r.horizon_value == 3
        assert r.horizon_unit == "month"

    def test_avoid_post(self):
        text = "Avoid YESBANK at current price ₹18. Very risky, fundamentals weak."
        results = rule_based_extract(text)
        assert len(results) >= 1
        assert results[0].action == "avoid"
        assert results[0].mention_price == 18.0

    def test_sell_post(self):
        text = "HDFC Bank ₹1700 sell karo. Price correction expected in next 2 months."
        results = rule_based_extract(text)
        assert len(results) >= 1
        assert results[0].action == "sell"

    def test_no_ticker_returns_empty(self):
        text = "Market is looking good today. Great time to invest!"
        results = rule_based_extract(text)
        assert results == []

    def test_tcs_long_term(self):
        text = "TCS at ₹3800 is a great buy for long term. Target ₹4500 in 1 year."
        results = rule_based_extract(text)
        assert len(results) >= 1
        r = results[0]
        assert r.raw_ticker == "TCS"
        assert r.action == "buy"
        assert r.horizon_value == 1
        assert r.horizon_unit == "year"

    def test_hinglish_entry(self):
        text = "TATAMOTORS mein entry lo ₹780 pe. Target ₹950, time frame 6 months."
        results = rule_based_extract(text)
        assert len(results) >= 1
        assert results[0].action == "buy"
        assert results[0].mention_price == 780.0

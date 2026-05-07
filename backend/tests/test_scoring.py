"""Tests for scoring agent logic."""
import pytest
from app.agents.scoring_agent import compute_return, classify_return


class TestComputeReturn:
    def test_buy_profit(self):
        r = compute_return("buy", 100.0, 120.0)
        assert abs(r - 0.20) < 1e-6

    def test_buy_loss(self):
        r = compute_return("buy", 100.0, 80.0)
        assert abs(r - (-0.20)) < 1e-6

    def test_sell_profit(self):
        # Sell at 100, price fell to 80 -> profit
        r = compute_return("sell", 100.0, 80.0)
        assert abs(r - 0.20) < 1e-6

    def test_sell_loss(self):
        # Sell at 100, price rose to 120 -> loss
        r = compute_return("sell", 100.0, 120.0)
        assert abs(r - (-0.20)) < 1e-6

    def test_avoid_profit(self):
        # Avoid at 100, price fell to 80 -> good call
        r = compute_return("avoid", 100.0, 80.0)
        assert abs(r - 0.20) < 1e-6

    def test_hold_neutral(self):
        r = compute_return("hold", 100.0, 102.0)
        assert abs(r - 0.02) < 1e-6

    def test_zero_entry_price(self):
        r = compute_return("buy", 0.0, 100.0)
        assert r == 0.0


class TestClassifyReturn:
    def test_good(self):
        assert classify_return(0.10) == "good"
        assert classify_return(0.051) == "good"

    def test_bad(self):
        assert classify_return(-0.10) == "bad"
        assert classify_return(-0.051) == "bad"

    def test_neutral_above_threshold(self):
        assert classify_return(0.04) == "neutral"

    def test_neutral_below_threshold(self):
        assert classify_return(-0.03) == "neutral"

    def test_exact_good_threshold(self):
        # 5% exactly is NOT > 5%, so neutral
        assert classify_return(0.05) == "neutral"

    def test_custom_thresholds(self):
        assert classify_return(0.10, good_threshold=0.15) == "neutral"
        assert classify_return(-0.10, bad_threshold=-0.05) == "bad"


class TestScoringFormula:
    """Integration-style tests for the full scoring formula."""

    def test_reliance_buy_scenario(self):
        # Bought at 2400, now 2700 -> +12.5% -> good
        r = compute_return("buy", 2400.0, 2700.0)
        assert abs(r - 0.125) < 1e-6
        assert classify_return(r) == "good"

    def test_yesbank_avoid_scenario(self):
        # Avoided at 18, price dropped to 12 -> +33% return (good avoid)
        r = compute_return("avoid", 18.0, 12.0)
        assert r > 0.05
        assert classify_return(r) == "good"

    def test_hdfc_sell_scenario_loss(self):
        # Sold at 1700, price rose to 1900 -> bad sell
        r = compute_return("sell", 1700.0, 1900.0)
        assert r < -0.05
        assert classify_return(r) == "bad"

    def test_neutral_minimal_movement(self):
        # Bought at 100, now 102 -> +2% -> neutral
        r = compute_return("buy", 100.0, 102.0)
        assert classify_return(r) == "neutral"

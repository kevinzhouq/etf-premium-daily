import json
from datetime import date
from pathlib import Path

import pytest

from etf_premium.config import load_funds
from etf_premium.provider import MarketClosed, ProviderError, rows_from_records

ROOT = Path(__file__).parents[1]


def _records():
    return json.loads((ROOT / "tests" / "fixtures" / "etf_spot.json").read_text(encoding="utf-8"))


def test_fixture_maps_all_nine_funds_and_computes_premium():
    funds = load_funds(ROOT / "config" / "funds.yaml")
    rows = rows_from_records(_records(), funds, expected_date=date(2026, 8, 21))

    assert len(rows) == 9
    assert rows[0]["code"] == "159655"
    assert rows[-1]["premium_rate"] == pytest.approx(8.0)


def test_missing_one_fund_rejects_the_whole_batch():
    funds = load_funds(ROOT / "config" / "funds.yaml")

    with pytest.raises(ProviderError, match="缺失"):
        rows_from_records(_records()[:-1], funds, expected_date=date(2026, 8, 21))


def test_all_rows_from_previous_date_means_market_closed():
    funds = load_funds(ROOT / "config" / "funds.yaml")

    with pytest.raises(MarketClosed):
        rows_from_records(_records(), funds, expected_date=date(2026, 8, 22))

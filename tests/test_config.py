from pathlib import Path

import pytest

from etf_premium.config import ConfigError, load_funds

ROOT = Path(__file__).parents[1]


def test_production_fund_pool_is_the_expected_nine():
    funds = load_funds(ROOT / "config" / "funds.yaml")
    codes = [fund.code for fund in funds]

    assert len(codes) == 9
    assert "159612" in codes
    assert "513110" in codes
    assert "513310" not in codes
    assert codes.count("159941") == 1


def test_duplicate_codes_are_rejected(tmp_path):
    config = tmp_path / "funds.yaml"
    config.write_text(
        "funds:\n"
        "  - {code: '159941', market: SZ, display_name: A, enabled: true}\n"
        "  - {code: '159941', market: SZ, display_name: B, enabled: true}\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="重复"):
        load_funds(config)


@pytest.mark.parametrize("code,market", [("15994", "SZ"), ("15994A", "SZ"), ("159941", "HK")])
def test_invalid_code_or_market_is_rejected(tmp_path, code, market):
    config = tmp_path / "funds.yaml"
    config.write_text(
        f"funds:\n  - {{code: '{code}', market: {market}, display_name: A, enabled: true}}\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError):
        load_funds(config)

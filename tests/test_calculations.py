import pytest

from etf_premium.calculations import calculate_premium, sort_rows, validate_cross_check


def test_calculate_premium_in_percentage_points():
    assert calculate_premium(1.105, 1.0) == pytest.approx(10.5)
    assert calculate_premium(0.99, 1.0) == pytest.approx(-1.0)
    assert calculate_premium(1.0, 1.0) == pytest.approx(0.0)


def test_cross_check_uses_negative_discount_rate():
    validate_cross_check(10.5, -10.4, tolerance=0.15)

    with pytest.raises(ValueError, match="交叉校验"):
        validate_cross_check(10.5, -10.3, tolerance=0.15)


def test_sort_rows_uses_code_as_tie_breaker():
    rows = [
        {"code": "513110", "premium_rate": 2.0},
        {"code": "159941", "premium_rate": -1.0},
        {"code": "159612", "premium_rate": 2.0},
    ]

    assert [row["code"] for row in sort_rows(rows)] == ["159941", "159612", "513110"]

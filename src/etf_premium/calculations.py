from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any


def calculate_premium(latest_price: float, iopv: float) -> float:
    latest_price = float(latest_price)
    iopv = float(iopv)
    if not math.isfinite(latest_price) or latest_price <= 0:
        raise ValueError("最新价必须是正数")
    if not math.isfinite(iopv) or iopv <= 0:
        raise ValueError("IOPV 必须是正数")
    return (latest_price / iopv - 1.0) * 100.0


def validate_cross_check(
    premium_rate: float, discount_rate: float, *, tolerance: float = 0.15
) -> None:
    discount_rate = float(discount_rate)
    if not math.isfinite(discount_rate):
        raise ValueError("基金折价率为空或无效")
    provider_premium = -discount_rate
    if abs(premium_rate - provider_premium) > tolerance + 1e-9:
        raise ValueError(
            f"溢价率交叉校验失败：计算值 {premium_rate:.4f}%，"
            f"供应商隐含值 {provider_premium:.4f}%"
        )


def sort_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (float(row["premium_rate"]), str(row["code"])))

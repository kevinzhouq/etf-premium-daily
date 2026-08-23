from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any

from .calculations import calculate_premium, validate_cross_check
from .models import FundConfig


class ProviderError(RuntimeError):
    pass


class MarketClosed(ProviderError):
    pass


def _number(value: Any, field: str, code: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ProviderError(f"{code} 的{field}无效：{value!r}") from exc
    if not math.isfinite(result):
        raise ProviderError(f"{code} 的{field}为空或无效")
    return result


def _iso_datetime(value: Any, code: str) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text).isoformat()
    except ValueError as exc:
        raise ProviderError(f"{code} 的更新时间无效：{text!r}") from exc


def rows_from_records(
    records: list[dict[str, Any]],
    funds: list[FundConfig],
    *,
    expected_date: date,
    tolerance: float = 0.15,
) -> list[dict[str, Any]]:
    wanted = {fund.code: fund for fund in funds}
    selected = {str(item.get("代码", "")).zfill(6): item for item in records if str(item.get("代码", "")).zfill(6) in wanted}
    missing = sorted(set(wanted) - set(selected))
    if missing:
        raise ProviderError(f"行情缺失：{', '.join(missing)}")

    dates: set[date] = set()
    result: list[dict[str, Any]] = []
    for fund in funds:
        raw = selected[fund.code]
        try:
            data_date = date.fromisoformat(str(raw.get("数据日期", ""))[:10])
        except ValueError as exc:
            raise ProviderError(f"{fund.code} 的数据日期无效") from exc
        dates.add(data_date)

        latest_price = _number(raw.get("最新价"), "最新价", fund.code)
        iopv = _number(raw.get("IOPV实时估值"), "IOPV", fund.code)
        discount_rate = _number(raw.get("基金折价率"), "基金折价率", fund.code)
        try:
            premium_rate = calculate_premium(latest_price, iopv)
            validate_cross_check(premium_rate, discount_rate, tolerance=tolerance)
        except ValueError as exc:
            raise ProviderError(f"{fund.code}：{exc}") from exc

        result.append(
            {
                "code": fund.code,
                "market": fund.market,
                "display_name": fund.display_name,
                "source_name": str(raw.get("名称", "")).strip(),
                "latest_price": latest_price,
                "iopv": iopv,
                "discount_rate": discount_rate,
                "premium_rate": premium_rate,
                "data_date": data_date.isoformat(),
                "source_updated_at": _iso_datetime(raw.get("更新时间"), fund.code),
            }
        )

    if len(dates) != 1:
        raise ProviderError("基金数据日期不一致，拒绝混用新旧行情")
    only_date = next(iter(dates))
    if only_date < expected_date:
        raise MarketClosed(f"数据日期为 {only_date}，{expected_date} 不是有效交易日")
    if only_date > expected_date:
        raise ProviderError(f"行情日期 {only_date} 晚于运行日期 {expected_date}")
    return result


class AkShareProvider:
    source_name = "AkShare / 东方财富"

    def fetch(self, funds: list[FundConfig], expected_date: date) -> list[dict[str, Any]]:
        try:
            import akshare as ak

            frame = ak.fund_etf_spot_em()
        except Exception as exc:  # external provider failures are normalized here
            raise ProviderError(f"AkShare 行情获取失败：{exc}") from exc
        records = frame.to_dict(orient="records")
        return rows_from_records(records, funds, expected_date=expected_date)

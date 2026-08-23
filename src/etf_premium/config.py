from __future__ import annotations

import re
from pathlib import Path

import yaml

from .models import FundConfig


class ConfigError(ValueError):
    pass


def load_funds(path: Path) -> list[FundConfig]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"无法读取基金配置：{exc}") from exc

    items = raw.get("funds")
    if not isinstance(items, list):
        raise ConfigError("配置必须包含 funds 列表")

    funds: list[FundConfig] = []
    seen: set[str] = set()
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise ConfigError(f"第 {index} 项不是对象")
        code = str(item.get("code", "")).strip()
        market = str(item.get("market", "")).strip().upper()
        display_name = str(item.get("display_name", "")).strip()
        enabled = item.get("enabled", True)

        if not re.fullmatch(r"\d{6}", code):
            raise ConfigError(f"ETF 代码必须是六位数字：{code!r}")
        if market not in {"SH", "SZ"}:
            raise ConfigError(f"{code} 的市场必须为 SH 或 SZ")
        if not display_name:
            raise ConfigError(f"{code} 缺少展示名称")
        if not isinstance(enabled, bool):
            raise ConfigError(f"{code} 的 enabled 必须为布尔值")
        if code in seen:
            raise ConfigError(f"ETF 代码重复：{code}")
        seen.add(code)
        if enabled:
            funds.append(FundConfig(code, market, display_name, enabled))

    if not funds:
        raise ConfigError("至少需要启用一只 ETF")
    return funds

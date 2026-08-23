from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from .calculations import sort_rows
from .config import load_funds
from .history import add_deltas, latest_snapshot, load_snapshots
from .models import FundConfig
from .provider import AkShareProvider, MarketClosed, ProviderError
from .site import build_site, build_waiting_site

BEIJING = ZoneInfo("Asia/Shanghai")


class PipelineStatus(str, Enum):
    FRESH = "fresh"
    CACHED = "cached"
    SKIPPED = "skipped"
    FAILED = "failed"


class DataProvider(Protocol):
    source_name: str

    def fetch(self, funds: list[FundConfig], expected_date: Any) -> list[dict[str, Any]]: ...


class PipelineError(RuntimeError):
    pass


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _base_result(now: datetime, status: PipelineStatus) -> dict[str, Any]:
    return {
        "trade_date": now.date().isoformat(),
        "captured_at": now.isoformat(),
        "source": "",
        "status": status.value,
        "warning": None,
        "funds": [],
        "snapshot_changed": False,
        "should_deploy": False,
        "should_notify": False,
    }


def run_pipeline(
    *,
    config_path: Path,
    snapshot_dir: Path,
    output_dir: Path,
    provider: DataProvider | None = None,
    now: datetime | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    now = (now or datetime.now(BEIJING)).astimezone(BEIJING)
    result = _base_result(now, PipelineStatus.FRESH)
    funds = load_funds(config_path)
    snapshots = load_snapshots(snapshot_dir)
    if now.weekday() >= 5 and not force_refresh:
        result.update(
            status=PipelineStatus.SKIPPED.value,
            warning="周末不运行行情抓取",
            source="none",
        )
        if not snapshots:
            build_waiting_site(
                captured_at=result["captured_at"], output_dir=output_dir, reason=result["warning"]
            )
            result["should_deploy"] = True
        _write_json(output_dir / "run_result.json", result)
        return result

    active_provider = provider or AkShareProvider()
    try:
        rows = active_provider.fetch(funds, now.date())
    except MarketClosed as exc:
        result.update(
            status=PipelineStatus.SKIPPED.value,
            warning=str(exc),
            source=active_provider.source_name,
        )
        if not snapshots:
            build_waiting_site(
                captured_at=result["captured_at"], output_dir=output_dir, reason=result["warning"]
            )
            result["should_deploy"] = True
        _write_json(output_dir / "run_result.json", result)
        return result
    except ProviderError as exc:
        cached = latest_snapshot(snapshots)
        if cached is None:
            result.update(
                status=PipelineStatus.FAILED.value,
                warning=str(exc),
                source=active_provider.source_name,
            )
            _write_json(output_dir / "run_result.json", result)
            raise PipelineError(f"行情失败且没有可用缓存：{exc}") from exc

        cached_date = datetime.fromisoformat(cached["trade_date"]).date()
        cached_rows = add_deltas(deepcopy(cached["funds"]), snapshots, cached_date)
        result.update(
            trade_date=cached["trade_date"],
            source=cached["source"],
            status=PipelineStatus.CACHED.value,
            warning=f"{exc}；已整表回退到 {cached['trade_date']} 的有效快照",
            funds=sort_rows(cached_rows),
            should_deploy=True,
            should_notify=True,
        )
        build_site(result, output_dir, history=snapshots)
        _write_json(output_dir / "run_result.json", result)
        return result

    snapshot = {
        "trade_date": now.date().isoformat(),
        "captured_at": now.isoformat(),
        "source": active_provider.source_name,
        "status": PipelineStatus.FRESH.value,
        "funds": rows,
    }
    snapshot_path = snapshot_dir / f"{now.date().isoformat()}.json"
    existing = None
    if snapshot_path.exists():
        try:
            existing = json.loads(snapshot_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            existing = None
    if (
        not existing
        or existing.get("funds") != rows
        or existing.get("source") != snapshot["source"]
    ):
        _write_json(snapshot_path, snapshot)
        result["snapshot_changed"] = True
    else:
        snapshot = existing

    refreshed_history = load_snapshots(snapshot_dir)
    enriched = add_deltas(deepcopy(snapshot["funds"]), refreshed_history, now.date())
    result.update(
        trade_date=snapshot["trade_date"],
        captured_at=snapshot["captured_at"],
        source=snapshot["source"],
        funds=sort_rows(enriched),
        should_deploy=True,
        should_notify=True,
    )
    build_site(result, output_dir, history=refreshed_history)
    _write_json(output_dir / "run_result.json", result)
    return result

from __future__ import annotations

import json
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path
from typing import Any


def load_snapshots(directory: Path) -> list[dict[str, Any]]:
    if not directory.exists():
        return []
    snapshots: list[dict[str, Any]] = []
    for path in sorted(directory.glob("????-??-??.json")):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
            date.fromisoformat(item["trade_date"])
            if item.get("status") == "fresh" and isinstance(item.get("funds"), list):
                snapshots.append(item)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            continue
    return snapshots


def latest_snapshot(snapshots: list[dict[str, Any]]) -> dict[str, Any] | None:
    return max(snapshots, key=lambda item: item["trade_date"], default=None)


def _find_snapshot_before(
    snapshots: list[dict[str, Any]], cutoff: date, *, max_age_days: int | None = None
) -> dict[str, Any] | None:
    candidates = [
        item for item in snapshots if date.fromisoformat(item["trade_date"]) <= cutoff
    ]
    if not candidates:
        return None
    result = max(candidates, key=lambda item: item["trade_date"])
    if max_age_days is not None:
        age = (cutoff - date.fromisoformat(result["trade_date"])).days
        if age > max_age_days:
            return None
    return result


def add_deltas(
    rows: list[dict[str, Any]], snapshots: list[dict[str, Any]], current_date: date
) -> list[dict[str, Any]]:
    previous = _find_snapshot_before(snapshots, current_date - timedelta(days=1))
    target_30d = current_date - timedelta(days=30)
    previous_30d = _find_snapshot_before(snapshots, target_30d, max_age_days=7)

    def rates(snapshot: dict[str, Any] | None) -> dict[str, float]:
        if not snapshot:
            return {}
        return {str(row["code"]): float(row["premium_rate"]) for row in snapshot["funds"]}

    previous_rates = rates(previous)
    rates_30d = rates(previous_30d)
    enriched = deepcopy(rows)
    for row in enriched:
        code = str(row["code"])
        current = float(row["premium_rate"])
        row["delta_previous"] = (
            current - previous_rates[code] if code in previous_rates else None
        )
        row["delta_30d"] = current - rates_30d[code] if code in rates_30d else None
    return enriched

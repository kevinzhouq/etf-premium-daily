import json
from datetime import date

from etf_premium.history import add_deltas, load_snapshots


def _write_snapshot(directory, day, premium):
    payload = {
        "trade_date": day,
        "captured_at": f"{day}T16:30:00+08:00",
        "source": "fixture",
        "status": "fresh",
        "funds": [{"code": "159941", "premium_rate": premium}],
    }
    (directory / f"{day}.json").write_text(json.dumps(payload), encoding="utf-8")


def test_previous_and_30_day_deltas_use_valid_snapshots(tmp_path):
    _write_snapshot(tmp_path, "2026-07-22", 1.0)
    _write_snapshot(tmp_path, "2026-08-20", 2.0)
    snapshots = load_snapshots(tmp_path)

    rows = add_deltas(
        [{"code": "159941", "premium_rate": 2.5}], snapshots, date(2026, 8, 21)
    )

    assert rows[0]["delta_previous"] == 0.5
    assert rows[0]["delta_30d"] == 1.5


def test_30_day_delta_is_missing_when_snapshot_is_too_old(tmp_path):
    _write_snapshot(tmp_path, "2026-07-14", 1.0)
    snapshots = load_snapshots(tmp_path)

    rows = add_deltas(
        [{"code": "159941", "premium_rate": 2.5}], snapshots, date(2026, 8, 21)
    )

    assert rows[0]["delta_30d"] is None

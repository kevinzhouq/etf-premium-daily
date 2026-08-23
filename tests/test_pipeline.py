import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from etf_premium.config import load_funds
from etf_premium.pipeline import PipelineStatus, run_pipeline
from etf_premium.provider import ProviderError

ROOT = Path(__file__).parents[1]


class FixtureProvider:
    source_name = "fixture"

    def fetch(self, funds, expected_date):
        records = json.loads(
            (ROOT / "tests" / "fixtures" / "etf_spot.json").read_text(encoding="utf-8")
        )
        from etf_premium.provider import rows_from_records

        return rows_from_records(records, funds, expected_date=expected_date)


class BrokenProvider:
    source_name = "broken"

    def fetch(self, funds, expected_date):
        raise ProviderError("upstream unavailable")


NOW = datetime(2026, 8, 21, 16, 30, tzinfo=ZoneInfo("Asia/Shanghai"))


def test_fresh_pipeline_writes_one_complete_snapshot_and_site(tmp_path):
    result = run_pipeline(
        config_path=ROOT / "config" / "funds.yaml",
        snapshot_dir=tmp_path / "snapshots",
        output_dir=tmp_path / "site",
        provider=FixtureProvider(),
        now=NOW,
    )

    assert result["status"] == PipelineStatus.FRESH.value
    assert len(result["funds"]) == 9
    assert (tmp_path / "snapshots" / "2026-08-21.json").exists()
    assert (tmp_path / "site" / "index.html").exists()


def test_provider_failure_uses_whole_latest_snapshot(tmp_path):
    run_pipeline(
        config_path=ROOT / "config" / "funds.yaml",
        snapshot_dir=tmp_path / "snapshots",
        output_dir=tmp_path / "site",
        provider=FixtureProvider(),
        now=NOW,
    )
    result = run_pipeline(
        config_path=ROOT / "config" / "funds.yaml",
        snapshot_dir=tmp_path / "snapshots",
        output_dir=tmp_path / "site2",
        provider=BrokenProvider(),
        now=datetime(2026, 8, 24, 16, 30, tzinfo=ZoneInfo("Asia/Shanghai")),
    )

    assert result["status"] == PipelineStatus.CACHED.value
    assert len(result["funds"]) == 9
    assert "upstream unavailable" in result["warning"]
    assert not (tmp_path / "snapshots" / "2026-08-24.json").exists()


def test_weekend_is_skipped_without_calling_provider(tmp_path):
    class MustNotRun:
        source_name = "unused"

        def fetch(self, funds, expected_date):
            raise AssertionError("provider should not be called")

    result = run_pipeline(
        config_path=ROOT / "config" / "funds.yaml",
        snapshot_dir=tmp_path / "snapshots",
        output_dir=tmp_path / "site",
        provider=MustNotRun(),
        now=datetime(2026, 8, 22, 16, 30, tzinfo=ZoneInfo("Asia/Shanghai")),
    )

    assert result["status"] == PipelineStatus.SKIPPED.value
    assert not (tmp_path / "snapshots").exists()

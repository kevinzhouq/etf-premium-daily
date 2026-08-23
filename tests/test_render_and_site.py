from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image

from etf_premium.render import render_ranking
from etf_premium.site import build_site


def _result():
    return {
        "trade_date": "2026-08-21",
        "captured_at": datetime(2026, 8, 21, 16, 30, tzinfo=ZoneInfo("Asia/Shanghai")).isoformat(),
        "source": "fixture",
        "status": "fresh",
        "warning": None,
        "funds": [
            {
                "code": f"159{index:03d}",
                "display_name": f"测试基金{index}",
                "premium_rate": float(index),
                "delta_previous": -0.1,
                "delta_30d": 0.2,
            }
            for index in range(1, 10)
        ],
    }


def test_image_contains_nine_rows_without_overflow(tmp_path):
    path = tmp_path / "latest.png"
    render_ranking(_result(), path)

    with Image.open(path) as image:
        assert image.width == 1080
        assert image.height >= 1200
        assert image.getbbox() is not None


def test_site_contains_table_and_machine_readable_files(tmp_path):
    result = _result()
    build_site(result, tmp_path, history=[result])

    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert html.count("<tr data-code=") == 9
    assert "仅供信息参考，不构成投资建议" in html
    assert (tmp_path / "latest.json").exists()
    assert (tmp_path / "history.json").exists()
    assert (tmp_path / "latest.png").exists()

import pytest

from etf_premium.notify import NotificationError, build_markdown, send_serverchan


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"code": 0, "message": "SUCCESS"}


class FakeSession:
    def __init__(self):
        self.calls = []

    def post(self, url, data, timeout):
        self.calls.append((url, data, timeout))
        return FakeResponse()


def _result(status="fresh"):
    return {
        "trade_date": "2026-08-21",
        "captured_at": "2026-08-21T16:30:00+08:00",
        "source": "fixture",
        "status": status,
        "warning": "使用缓存" if status == "cached" else None,
        "funds": [
            {
                "code": "159941",
                "display_name": "广发纳斯达克100",
                "premium_rate": 2.0,
                "delta_previous": 0.1,
                "delta_30d": None,
            }
        ],
    }


def test_markdown_contains_public_image_and_table():
    title, markdown = build_markdown(_result(), "https://example.github.io/repo/")

    assert title == "ETF每日溢价率排行｜2026-08-21"
    assert "https://example.github.io/repo/latest.png" in markdown
    assert "广发纳斯达克100" in markdown


def test_cached_title_is_explicit():
    title, _ = build_markdown(_result("cached"), "https://example.github.io/repo/")
    assert title.startswith("[缓存]")


def test_serverchan_turbo_key_uses_private_endpoint(monkeypatch):
    session = FakeSession()
    monkeypatch.setattr("etf_premium.notify.time.sleep", lambda _: None)

    send_serverchan("sctp123tSECRET", "title", "body", session=session)

    assert session.calls[0][0] == "https://123.push.ft07.com/send/sctp123tSECRET.send"


def test_missing_sendkey_is_rejected():
    with pytest.raises(NotificationError, match="SENDKEY"):
        send_serverchan("", "title", "body", session=FakeSession())

from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import urljoin

import requests

from .render import format_pct


class NotificationError(RuntimeError):
    pass


def build_markdown(result: dict[str, Any], page_url: str) -> tuple[str, str]:
    page_url = page_url.rstrip("/") + "/"
    cached = result.get("status") == "cached"
    prefix = "[缓存]" if cached else ""
    title = f"{prefix}ETF每日溢价率排行｜{result['trade_date']}"
    lines = [
        f"![ETF每日溢价率排行榜]({urljoin(page_url, 'latest.png')})",
        "",
        "| 排名 | ETF | 溢价率 | 较昨天 | 较30天前 |",
        "|---:|---|---:|---:|---:|",
    ]
    for index, row in enumerate(result["funds"], start=1):
        lines.append(
            f"| {index} | {row['display_name']}（{row['code']}） | "
            f"{format_pct(row.get('premium_rate'))} | "
            f"{format_pct(row.get('delta_previous'), signed=True)} | "
            f"{format_pct(row.get('delta_30d'), signed=True)} |"
        )
    lines.extend(
        [
            "",
            f"数据时间：{str(result['captured_at']).replace('T', ' ')[:19]}（北京时间）  ",
            f"数据来源：{result['source']}  ",
            f"[查看完整网页]({page_url})",
            "",
            "> 仅供信息参考，不构成投资建议。",
        ]
    )
    if result.get("warning"):
        lines.insert(0, f"> **缓存提示：** {result['warning']}\n")
    return title, "\n".join(lines)


def _endpoint(sendkey: str) -> str:
    turbo = re.match(r"^sctp(\d+)t", sendkey)
    if turbo:
        return f"https://{turbo.group(1)}.push.ft07.com/send/{sendkey}.send"
    return f"https://sctapi.ftqq.com/{sendkey}.send"


def send_serverchan(
    sendkey: str,
    title: str,
    markdown: str,
    *,
    session: requests.Session | Any | None = None,
    retries: int = 3,
) -> dict[str, Any]:
    sendkey = sendkey.strip()
    if not sendkey:
        raise NotificationError("缺少 SERVERCHAN_SENDKEY")
    client = session or requests.Session()
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = client.post(
                _endpoint(sendkey), data={"title": title, "desp": markdown}, timeout=20
            )
            response.raise_for_status()
            payload = response.json()
            status_code = payload.get("code", payload.get("errno", 0))
            if status_code not in (0, "0", None):
                raise NotificationError(f"Server酱返回失败：{payload}")
            return payload
        except (requests.RequestException, ValueError, NotificationError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(attempt * 2)
    error_name = type(last_error).__name__ if last_error else "UnknownError"
    raise NotificationError(f"Server酱推送重试 {retries} 次后失败（{error_name}）")

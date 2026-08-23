from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .render import format_pct, render_ranking


def build_waiting_site(*, captured_at: str, output_dir: Path, reason: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    page = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ETF每日溢价率排序</title>
<style>body{{margin:0;background:#f6f8fb;color:#111827;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif}}main{{max-width:760px;margin:10vh auto;padding:24px}}article{{background:#fff;border:1px solid #e5e7eb;border-radius:16px;padding:36px;box-shadow:0 8px 30px rgba(15,23,42,.05)}}h1{{margin-top:0}}.status{{border-left:6px solid #3578e5;background:#eff6ff;padding:16px;margin:24px 0}}p{{line-height:1.8;color:#475569}}small{{color:#64748b}}</style>
</head><body><main><article><h1>ETF每日溢价率排序</h1>
<div class="status"><strong>等待首个交易日数据</strong></div>
<p>项目已经部署成功。当前没有可发布的有效行情快照；首个交易日任务完成后，本页会自动替换为完整的 ETF 溢价率排行榜。</p>
<p>本页不会使用测试数据或过期数据冒充实时行情。</p>
<small>检查时间：{html.escape(captured_at.replace("T", " ")[:19])}（北京时间）<br>原因：{html.escape(reason)}<br>仅供信息参考，不构成投资建议。</small>
</article></main></body></html>"""
    (output_dir / "index.html").write_text(page, encoding="utf-8")


def _json_write(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _cell(value: float | None, *, signed: bool = False) -> str:
    css = "neutral"
    if value is not None and value > 0:
        css = "positive"
    elif value is not None and value < 0:
        css = "negative"
    return f'<td class="number {css}">{format_pct(value, signed=signed)}</td>'


def build_site(result: dict[str, Any], output_dir: Path, *, history: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    render_ranking(result, output_dir / "latest.png")
    _json_write(output_dir / "latest.json", result)
    history_index = [
        {
            "trade_date": item["trade_date"],
            "captured_at": item["captured_at"],
            "status": item["status"],
            "source": item["source"],
            "funds": item["funds"],
        }
        for item in sorted(history, key=lambda item: item["trade_date"], reverse=True)
    ]
    _json_write(output_dir / "history.json", history_index)

    table_rows = []
    for index, row in enumerate(result["funds"], start=1):
        table_rows.append(
            f'<tr data-code="{html.escape(str(row["code"]))}">'
            f"<td>{index}</td>"
            f"<td><strong>{html.escape(str(row['display_name']))}</strong>"
            f'<span class="code">{html.escape(str(row["code"]))}</span></td>'
            f"{_cell(row.get('premium_rate'))}"
            f"{_cell(row.get('delta_previous'), signed=True)}"
            f"{_cell(row.get('delta_30d'), signed=True)}"
            "</tr>"
        )

    cached = result.get("status") == "cached"
    status_class = "warning" if cached else "info"
    status_text = (
        "缓存数据：本次抓取未通过校验，当前页面整表使用最近有效快照。"
        if cached
        else "数据完整性校验已通过，当前表格为完整的新鲜快照。"
    )
    warning_detail = html.escape(str(result.get("warning") or ""))
    page = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="ETF 每日溢价率排序">
  <title>ETF每日溢价率排序</title>
  <style>
    :root {{ color-scheme: light; --red:#c93636; --green:#169b62; --ink:#111827; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:#f6f8fb; color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif; }}
    main {{ max-width:1050px; margin:32px auto; padding:0 18px 48px; }}
    .card {{ background:white; border:1px solid #e5e7eb; border-radius:16px; padding:26px; box-shadow:0 8px 30px rgba(15,23,42,.05); }}
    h1 {{ margin:0 0 8px; font-size:34px; }} .meta {{ color:#64748b; margin-bottom:22px; }}
    .status {{ border-left:6px solid #3578e5; padding:14px 16px; background:#eff6ff; margin:20px 0; }}
    .status.warning {{ border-color:#f59e0b; background:#fff3e6; color:#7c2d12; }}
    .detail {{ display:block; font-size:13px; margin-top:5px; opacity:.75; }}
    .image {{ width:100%; height:auto; border:1px solid #e5e7eb; border-radius:10px; }}
    .table-wrap {{ overflow-x:auto; margin-top:26px; }} table {{ width:100%; border-collapse:collapse; min-width:720px; }}
    th,td {{ padding:15px 12px; border-bottom:1px solid #e5e7eb; text-align:left; }} th {{ background:#eef2f7; color:#334155; }}
    .number {{ text-align:right; font-weight:700; font-variant-numeric:tabular-nums; }} .positive {{ color:var(--red); }} .negative {{ color:var(--green); }}
    .code {{ color:#64748b; font-size:13px; margin-left:9px; }} footer {{ color:#64748b; margin-top:24px; font-size:14px; line-height:1.8; }}
    .links a {{ color:#2563eb; margin-right:16px; }}
  </style>
</head>
<body><main><article class="card">
  <h1>ETF每日溢价率排序</h1>
  <div class="meta">北京时间 {html.escape(str(result["captured_at"]).replace("T", " ")[:19])} · 交易日 {html.escape(str(result["trade_date"]))}</div>
  <div class="status {status_class}">{status_text}<span class="detail">{warning_detail}</span></div>
  <img class="image" src="latest.png" alt="ETF每日溢价率排行榜">
  <div class="table-wrap"><table>
    <thead><tr><th>序号</th><th>ETF名称</th><th class="number">溢价率</th><th class="number">较昨天</th><th class="number">较30天前</th></tr></thead>
    <tbody>{"".join(table_rows)}</tbody>
  </table></div>
  <footer>
    <div>数据来源：{html.escape(str(result["source"]))}。正数表示溢价，负数表示折价。</div>
    <div>仅供信息参考，不构成投资建议。</div>
    <div class="links"><a href="latest.json">最新 JSON</a><a href="history.json">历史 JSON</a></div>
  </footer>
</article></main></body></html>
"""
    (output_dir / "index.html").write_text(page, encoding="utf-8")

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1080
ROW_HEIGHT = 92


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    custom = os.getenv("ETF_FONT_PATH")
    candidates = [
        custom,
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else None,
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def format_pct(value: float | None, *, signed: bool = False) -> str:
    if value is None:
        return "—"
    if signed:
        return f"{value:+.2f}%"
    return f"{value:.2f}%"


def _value_color(value: float | None) -> str:
    if value is None or abs(value) < 0.000001:
        return "#334155"
    return "#C93636" if value > 0 else "#169B62"


def render_ranking(result: dict[str, Any], output_path: Path) -> None:
    rows = result["funds"]
    height = 340 + len(rows) * ROW_HEIGHT + 150
    image = Image.new("RGB", (WIDTH, height), "#FFFFFF")
    draw = ImageDraw.Draw(image)

    title_font = _font(52, bold=True)
    meta_font = _font(25)
    note_font = _font(27)
    header_font = _font(25, bold=True)
    row_font = _font(27)
    value_font = _font(28, bold=True)
    footer_font = _font(21)

    draw.text((42, 38), "ETF每日溢价率排序", font=title_font, fill="#111827")
    captured = str(result["captured_at"]).replace("T", " ")[:19]
    draw.text((44, 108), f"北京时间 {captured}", font=meta_font, fill="#64748B")

    cached = result.get("status") == "cached"
    note_top = 155
    draw.rounded_rectangle(
        (38, note_top, WIDTH - 38, note_top + 105),
        radius=10,
        fill="#FFF3E6" if cached else "#EFF6FF",
    )
    draw.rectangle(
        (38, note_top, 46, note_top + 105), fill="#F59E0B" if cached else "#3578E5"
    )
    note = (
        "缓存数据：本次行情未通过完整性校验，整表使用最近有效快照。"
        if cached
        else "按当前溢价率从低到高排序；变化值为溢价率百分点差。"
    )
    draw.text((64, note_top + 32), note, font=note_font, fill="#7C2D12" if cached else "#1E3A5F")

    table_top = 285
    draw.rounded_rectangle((38, table_top, WIDTH - 38, table_top + 62), radius=8, fill="#EEF2F7")
    headers = [(64, "序号"), (142, "ETF名称"), (650, "溢价率"), (820, "较昨天"), (1040, "较30天前")]
    for x, label in headers:
        anchor = "ra" if x >= 650 else "la"
        draw.text((x, table_top + 31), label, font=header_font, fill="#334155", anchor=anchor)

    y = table_top + 62
    for index, row in enumerate(rows, start=1):
        center_y = y + ROW_HEIGHT // 2
        draw.line((38, y + ROW_HEIGHT, WIDTH - 38, y + ROW_HEIGHT), fill="#E2E8F0", width=2)
        draw.text((72, center_y), str(index), font=row_font, fill="#64748B", anchor="mm")
        name = f"{row['display_name']}  {row['code']}"
        draw.text((142, center_y), name, font=row_font, fill="#111827", anchor="lm")
        for x, key, signed in [
            (650, "premium_rate", False),
            (820, "delta_previous", True),
            (1040, "delta_30d", True),
        ]:
            value = row.get(key)
            draw.text(
                (x, center_y),
                format_pct(value, signed=signed),
                font=value_font,
                fill=_value_color(value),
                anchor="rm",
            )
        y += ROW_HEIGHT

    footer_y = y + 34
    draw.text(
        (42, footer_y),
        f"数据来源：{result['source']}｜正数表示溢价，负数表示折价。",
        font=footer_font,
        fill="#64748B",
    )
    draw.text(
        (42, footer_y + 38),
        "仅供信息参考，不构成任何投资建议。",
        font=footer_font,
        fill="#64748B",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG", optimize=True)

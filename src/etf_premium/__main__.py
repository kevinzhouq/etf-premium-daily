from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .notify import build_markdown, send_serverchan
from .pipeline import PipelineError, run_pipeline


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ETF 每日溢价率排行榜")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="抓取、校验并生成快照和网站")
    run.add_argument("--config", type=Path, default=Path("config/funds.yaml"))
    run.add_argument("--snapshot-dir", type=Path, default=Path("data/snapshots"))
    run.add_argument("--output-dir", type=Path, default=Path("site"))
    run.add_argument("--force-refresh", action="store_true")

    notify = subparsers.add_parser("notify", help="根据运行结果发送 Server酱通知")
    notify.add_argument("--result", type=Path, default=Path("site/run_result.json"))
    notify.add_argument("--page-url", default=os.getenv("PAGE_URL", ""))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "run":
        try:
            result = run_pipeline(
                config_path=args.config,
                snapshot_dir=args.snapshot_dir,
                output_dir=args.output_dir,
                force_refresh=args.force_refresh,
            )
        except PipelineError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if not args.page_url:
        print("缺少 --page-url 或 PAGE_URL", file=sys.stderr)
        return 2
    result = json.loads(args.result.read_text(encoding="utf-8"))
    title, markdown = build_markdown(result, args.page_url)
    send_serverchan(os.getenv("SERVERCHAN_SENDKEY", ""), title, markdown)
    print(f"Server酱推送成功：{title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

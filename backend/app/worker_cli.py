from __future__ import annotations

import argparse
import json

from .core.config import settings
from .services.browser_worker import BrowserWorker


def main() -> None:
    parser = argparse.ArgumentParser(description="Boss Agent Playwright worker CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status")
    login_parser = subparsers.add_parser("login")
    login_parser.add_argument("--timeout", type=int, default=300)

    collect_parser = subparsers.add_parser("collect")
    collect_parser.add_argument("--keyword", default="前端")
    collect_parser.add_argument("--city", default="101010100")

    subparsers.add_parser("sync-messages")

    args = parser.parse_args()
    worker = BrowserWorker(
        base_url=settings.boss_base_url,
        state_dir=settings.browser_state_dir,
        headless=settings.browser_headless,
    )

    if args.command == "status":
        result = worker.status()
    elif args.command == "login":
        result = worker.manual_login(timeout_seconds=args.timeout)
    elif args.command == "collect":
        result = worker.collect_jobs(keyword=args.keyword, city=args.city)
    else:
        result = worker.sync_messages()

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spec_crawler",
        description="Specification crawler CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    crawl = subparsers.add_parser("crawl", help="Run crawl pipeline")
    crawl.add_argument("--policy", default="w3c", help="Policy name")
    crawl.add_argument("--maxPages", type=int, default=50, help="Max pages to fetch")

    subparsers.add_parser("audit", help="Audit crawl outputs")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "crawl":
        print(
            f"crawl skeleton: policy={args.policy}, maxPages={args.maxPages}. "
            "Implementation will be added in next tasks."
        )
        return 0

    if args.command == "audit":
        print("audit skeleton: implementation will be added in later tasks.")
        return 0

    parser.print_help()
    return 0

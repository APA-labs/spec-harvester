from __future__ import annotations

import argparse

from spec_harvester.application.audit import render_audit_report, run_audit
from spec_harvester.application.queue import run_crawl
from spec_harvester.infrastructure.config.policy_loader import load_policy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spec_harvester",
        description="Specification crawler CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    crawl = subparsers.add_parser("crawl", help="Run crawl pipeline")
    crawl.add_argument("--policy", default="w3c", help="Policy name")
    crawl.add_argument("--max-pages", "--maxPages", dest="max_pages", type=int, default=None)

    audit = subparsers.add_parser("audit", help="Audit crawl outputs")
    audit.add_argument("--manifest-root", default="storage/manifests")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "crawl":
        policy = load_policy(args.policy)
        result = run_crawl(policy=policy, max_pages=args.max_pages)
        print(
            "crawl completed "
            f"fetched={result.fetched} no_change={result.no_change} errors={result.errors} "
            f"manifest={result.manifest_path} log={result.log_path}"
        )
        return 0

    if args.command == "audit":
        report = run_audit(manifest_root=args.manifest_root)
        print(render_audit_report(report))
        return 0

    parser.print_help()
    return 0

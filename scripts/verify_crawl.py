#!/usr/bin/env python3
"""
Verify that a crawl run captured the expected pages for each policy.

Usage:
  python scripts/verify_crawl.py --input storage/raw/2026-02-28
  python scripts/verify_crawl.py --input storage/raw/2026-02-28 --policy apg mui
"""

import json
import sys
from pathlib import Path
from argparse import ArgumentParser

EXPECTED: dict[str, dict[str, str]] = {
    "apg": {
        "button":       "/apg/patterns/button",
        "text-input":   "/apg/patterns/textbox",
        "modal-dialog": "/apg/patterns/dialog-modal",
        "tabs":         "/apg/patterns/tabs",
        "tooltip":      "/apg/patterns/tooltip",
        "disclosure":   "/apg/patterns/disclosure",
        "accordion":    "/apg/patterns/accordion",
        "combobox":     "/apg/patterns/combobox",
    },
    "mui": {
        "button":       "react-button",
        "text-input":   "react-text-field",
        "modal-dialog": "react-dialog",
        "toggle":       "react-toggle-button",
        "tabs":         "react-tabs",
        "tooltip":      "react-tooltip",
        "accordion":    "react-accordion",
    },
    "radix": {
        "modal-dialog": "components/dialog",
        "toggle":       "components/toggle",
        "tabs":         "components/tabs",
        "tooltip":      "components/tooltip",
        "disclosure":   "components/accordion",
    },
    "antd": {
        "button":       "components/button",
        "text-input":   "components/input",
        "modal-dialog": "components/modal",
        "toggle":       "components/switch",
        "tabs":         "components/tabs",
        "tooltip":      "components/tooltip",
        "disclosure":   "components/collapse",
    },
}

DOMAIN_POLICY: dict[str, str] = {
    "www.w3.org":       "apg",
    "mui.com":          "mui",
    "www.radix-ui.com": "radix",
    "ant.design":       "antd",
}


def load_crawled_urls(input_dir: Path) -> list[str]:
    urls = []
    for meta_file in input_dir.glob("*.meta.json"):
        try:
            data = json.loads(meta_file.read_text())
            url = data.get("resolved_url") or data.get("url") or ""
            if url:
                urls.append(url)
        except (json.JSONDecodeError, OSError):
            pass
    return urls


def detect_policy(urls: list[str]) -> set[str]:
    found = set()
    for url in urls:
        for domain, policy in DOMAIN_POLICY.items():
            if domain in url:
                found.add(policy)
    return found


def verify(input_dir: Path, policies: list[str]) -> bool:
    if not input_dir.exists():
        print(f"✗ Directory not found: {input_dir}")
        return False

    urls = load_crawled_urls(input_dir)
    if not urls:
        print(f"✗ No .meta.json files found in {input_dir}")
        return False

    detected = detect_policy(urls)
    print(f"Crawled URLs: {len(urls)} total")
    print(f"Detected policies: {', '.join(sorted(detected)) or 'none'}\n")

    if not policies:
        policies = sorted(detected) or list(EXPECTED.keys())

    all_ok = True

    for policy in policies:
        if policy not in EXPECTED:
            print(f"⚠  Unknown policy '{policy}' — skipping")
            continue

        print(f"── {policy.upper()} ──────────────────────")
        patterns = EXPECTED[policy]
        found_count = 0

        for pattern_id, url_seg in patterns.items():
            matched = next((u for u in urls if url_seg in u), None)
            if matched:
                print(f"  ✓ {pattern_id:<16} {matched}")
                found_count += 1
            else:
                print(f"  ✗ {pattern_id:<16} (expected segment: {url_seg})")
                all_ok = False

        print(f"  {found_count}/{len(patterns)} patterns found\n")

    return all_ok


def main() -> None:
    parser = ArgumentParser(description="Verify crawl output for a11y pattern pages")
    parser.add_argument("--input", required=True, help="Crawl output directory (storage/raw/YYYY-MM-DD)")
    parser.add_argument("--policy", nargs="*", help="Policies to check (default: auto-detect)")
    args = parser.parse_args()

    ok = verify(Path(args.input), args.policy or [])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

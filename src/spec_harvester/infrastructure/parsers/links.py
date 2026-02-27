from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, urlunsplit

from spec_harvester.domain.url import normalize_url


class _AnchorHrefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return

        for key, value in attrs:
            if key.lower() == "href" and value:
                self.hrefs.append(value)
                break


def extract_links(
    html: str,
    base_url: str,
    *,
    allowed_domains: list[str] | None = None,
    allowed_paths_prefix: list[str] | None = None,
    disallowed_paths_prefix: list[str] | None = None,
) -> list[str]:
    parser = _AnchorHrefParser()
    parser.feed(html)

    allowed_domains_normalized = {d.lower() for d in (allowed_domains or [])}
    allowed_paths = allowed_paths_prefix or []
    disallowed_paths = disallowed_paths_prefix or []

    out: list[str] = []
    seen: set[str] = set()

    for raw_href in parser.hrefs:
        href = raw_href.strip()
        if not href:
            continue

        low = href.lower()
        if low.startswith("#") or low.startswith("mailto:") or low.startswith("javascript:"):
            continue

        absolute = urljoin(base_url, href)
        split = urlsplit(absolute)

        if split.scheme.lower() not in {"http", "https"} or not split.netloc:
            continue

        cleaned = urlunsplit((split.scheme, split.netloc, split.path, split.query, ""))

        if allowed_domains_normalized and not _is_allowed_domain(split.hostname or "", allowed_domains_normalized):
            continue

        path = split.path or "/"
        if allowed_paths and not any(path.startswith(prefix) for prefix in allowed_paths):
            continue
        if any(path.startswith(prefix) for prefix in disallowed_paths):
            continue

        normalized = normalize_url(cleaned)
        if normalized in seen:
            continue

        seen.add(normalized)
        out.append(normalized)

    return out


def _is_allowed_domain(hostname: str, allowed_domains: set[str]) -> bool:
    host = hostname.lower()
    return any(host == domain or host.endswith(f".{domain}") for domain in allowed_domains)

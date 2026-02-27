from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def normalize_url(url: str) -> str:
    """Normalize URLs for dedup-safe crawling."""
    split = urlsplit(url)

    if not split.scheme or not split.netloc:
        raise ValueError(f"invalid absolute URL: {url}")

    scheme = split.scheme.lower()
    hostname = (split.hostname or "").lower()

    port = split.port
    if port is not None and not (
        (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    ):
        netloc = f"{hostname}:{port}"
    else:
        netloc = hostname

    path = split.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    query_items = parse_qsl(split.query, keep_blank_values=True)
    filtered_query = [(k, v) for k, v in query_items if not k.lower().startswith("utm_")]
    query = urlencode(sorted(filtered_query), doseq=True)

    return urlunsplit((scheme, netloc, path, query, ""))

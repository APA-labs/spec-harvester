from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Callable, Mapping

LOGGER = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


@dataclass(frozen=True)
class ResponseData:
    status: int
    headers: dict[str, str]
    body: bytes
    final_url: str
    content_type: str
    duration_ms: int


@dataclass(frozen=True)
class FetchError(RuntimeError):
    url: str
    reason: str
    attempts: int
    duration_ms: int
    status_code: int | None = None

    def __str__(self) -> str:
        return (
            "FetchError("
            f"url={self.url}, reason={self.reason}, attempts={self.attempts}, "
            f"status_code={self.status_code}, duration_ms={self.duration_ms}"
            ")"
        )


def fetch(
    url: str,
    *,
    timeout_s: float = 10.0,
    max_retries: int = 2,
    backoff_s: float = 0.5,
    getter: Callable[[str, float], object] | None = None,
    logger: logging.Logger | None = None,
    sleeper: Callable[[float], None] | None = None,
) -> ResponseData:
    if timeout_s <= 0:
        raise ValueError("timeout_s must be > 0")
    if max_retries < 0:
        raise ValueError("max_retries must be >= 0")

    fetcher = getter or _default_http_get
    log = logger or LOGGER
    sleep_fn = sleeper or time.sleep

    started = time.monotonic()
    attempts = max_retries + 1

    for attempt in range(1, attempts + 1):
        try:
            response = fetcher(url, timeout_s)
        except Exception as exc:
            if attempt < attempts:
                sleep_fn(backoff_s * attempt)
                continue

            duration_ms = _elapsed_ms(started)
            log.error(
                "fetch_error url=%s duration_ms=%s attempts=%s reason=network_error",
                url,
                duration_ms,
                attempt,
            )
            raise FetchError(
                url=url,
                reason=f"network_error: {exc}",
                attempts=attempt,
                duration_ms=duration_ms,
            ) from exc

        status = int(getattr(response, "status_code"))

        if status in RETRYABLE_STATUS_CODES and attempt < attempts:
            sleep_fn(backoff_s * attempt)
            continue

        if status in RETRYABLE_STATUS_CODES:
            duration_ms = _elapsed_ms(started)
            log.error(
                "fetch_error url=%s duration_ms=%s attempts=%s reason=http_retry_exhausted status=%s",
                url,
                duration_ms,
                attempt,
                status,
            )
            raise FetchError(
                url=url,
                reason="http_retry_exhausted",
                status_code=status,
                attempts=attempt,
                duration_ms=duration_ms,
            )

        duration_ms = _elapsed_ms(started)
        headers = dict(_response_headers(response))
        final_url = str(getattr(response, "url", url))
        content_type = headers.get("content-type", "")

        log.info(
            "fetch_success url=%s status=%s duration_ms=%s final_url=%s",
            url,
            status,
            duration_ms,
            final_url,
        )

        return ResponseData(
            status=status,
            headers=headers,
            body=bytes(getattr(response, "content", b"")),
            final_url=final_url,
            content_type=content_type,
            duration_ms=duration_ms,
        )

    raise AssertionError("unreachable")


def _response_headers(response: object) -> Mapping[str, str]:
    headers = getattr(response, "headers", {})
    if isinstance(headers, Mapping):
        return {str(k).lower(): str(v) for k, v in headers.items()}
    return {}


def _elapsed_ms(started: float) -> int:
    return max(0, int((time.monotonic() - started) * 1000))


def _default_http_get(url: str, timeout_s: float) -> object:
    import httpx

    with httpx.Client(timeout=timeout_s, follow_redirects=True) as client:
        return client.get(url)

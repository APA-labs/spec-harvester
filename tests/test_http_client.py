from __future__ import annotations

from dataclasses import dataclass

import pytest

from spec_crawler.infrastructure.http.http_client import FetchError, fetch


@dataclass
class _FakeResponse:
    status_code: int
    headers: dict[str, str]
    content: bytes
    url: str


class _SeqGetter:
    def __init__(self, values):
        self.values = list(values)
        self.calls = 0

    def __call__(self, url: str, timeout_s: float):
        self.calls += 1
        value = self.values.pop(0)
        if isinstance(value, Exception):
            raise value
        return value


def test_fetch_retries_429_then_success() -> None:
    getter = _SeqGetter(
        [
            _FakeResponse(429, {"content-type": "text/html"}, b"", "https://a.test"),
            _FakeResponse(200, {"content-type": "text/html"}, b"ok", "https://a.test/final"),
        ]
    )

    sleeps: list[float] = []
    out = fetch(
        "https://a.test",
        timeout_s=2.0,
        max_retries=2,
        getter=getter,
        sleeper=sleeps.append,
    )

    assert getter.calls == 2
    assert sleeps == [0.5]
    assert out.status == 200
    assert out.final_url == "https://a.test/final"
    assert out.body == b"ok"


def test_fetch_404_not_retried() -> None:
    getter = _SeqGetter([_FakeResponse(404, {"content-type": "text/html"}, b"missing", "https://a.test/m")])

    out = fetch("https://a.test/m", getter=getter, max_retries=3)

    assert getter.calls == 1
    assert out.status == 404
    assert out.content_type == "text/html"


def test_fetch_retry_exhausted_raises_structured_error() -> None:
    getter = _SeqGetter(
        [
            _FakeResponse(503, {"content-type": "text/html"}, b"", "https://a.test"),
            _FakeResponse(503, {"content-type": "text/html"}, b"", "https://a.test"),
            _FakeResponse(503, {"content-type": "text/html"}, b"", "https://a.test"),
        ]
    )

    with pytest.raises(FetchError) as exc:
        fetch("https://a.test", getter=getter, max_retries=2, sleeper=lambda _: None)

    assert exc.value.status_code == 503
    assert exc.value.attempts == 3
    assert exc.value.duration_ms >= 0


def test_fetch_network_error_exhausted_raises_structured_error() -> None:
    getter = _SeqGetter([RuntimeError("boom")])

    with pytest.raises(FetchError) as exc:
        fetch("https://a.test", getter=getter, max_retries=0)

    assert "network_error" in exc.value.reason
    assert exc.value.status_code is None
    assert exc.value.attempts == 1


def test_fetch_timeout_validation() -> None:
    with pytest.raises(ValueError):
        fetch("https://a.test", timeout_s=0)

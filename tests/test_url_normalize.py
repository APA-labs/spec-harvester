from __future__ import annotations

import pytest

from spec_crawler.domain.url import normalize_url


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("HTTPS://WWW.W3.ORG/TR/", "https://www.w3.org/TR"),
        ("https://www.w3.org/TR/#section", "https://www.w3.org/TR"),
        ("https://www.w3.org/TR/?utm_source=x", "https://www.w3.org/TR"),
        (
            "https://www.w3.org/TR/?a=1&utm_medium=email&b=2",
            "https://www.w3.org/TR?a=1&b=2",
        ),
        (
            "https://www.w3.org/TR/?b=2&a=1",
            "https://www.w3.org/TR?a=1&b=2",
        ),
        (
            "https://www.w3.org/TR/page/?utm_campaign=spring&k=v#frag",
            "https://www.w3.org/TR/page?k=v",
        ),
        ("HTTP://WWW.W3.ORG:80/TR/", "http://www.w3.org/TR"),
        ("HTTPS://WWW.W3.ORG:443/TR/", "https://www.w3.org/TR"),
        ("https://www.w3.org:444/TR/", "https://www.w3.org:444/TR"),
        ("https://www.w3.org", "https://www.w3.org/"),
        (
            "https://www.w3.org/TR/?UTM_Source=abc&x=1",
            "https://www.w3.org/TR?x=1",
        ),
    ],
)
def test_normalize_url_rules(raw: str, expected: str) -> None:
    assert normalize_url(raw) == expected


def test_invalid_url_raises() -> None:
    with pytest.raises(ValueError):
        normalize_url("/TR/")

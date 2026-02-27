from __future__ import annotations

from spec_harvester.infrastructure.parsers.links import extract_links


def test_extract_links_w3c_tr_sample_with_policy_filters() -> None:
    html = """
    <html><body>
      <a href="/TR/wai-aria/">WAI-ARIA</a>
      <a href="https://www.w3.org/TR/html-aam-1.0/">HTML AAM</a>
      <a href="wai-aria/">Relative duplicate</a>
      <a href="/blog/post">Blog</a>
      <a href="https://example.com/TR/other">Other domain</a>
      <a href="#section">Fragment only</a>
      <a href="javascript:void(0)">JS</a>
      <a href="mailto:test@w3.org">Mail</a>
    </body></html>
    """

    links = extract_links(
        html,
        "https://www.w3.org/TR/",
        allowed_domains=["www.w3.org"],
        allowed_paths_prefix=["/TR/"],
        disallowed_paths_prefix=["/blog/"],
    )

    assert links == [
        "https://www.w3.org/TR/wai-aria",
        "https://www.w3.org/TR/html-aam-1.0",
    ]


def test_extract_links_defaults_relative_to_absolute_and_fragment_removed() -> None:
    html = """
    <a href="./spec-one/#intro">One</a>
    <a href="https://www.w3.org/TR/spec-two/#x">Two</a>
    <a href="ftp://example.com/file">Ignore non-http</a>
    """

    links = extract_links(html, "https://www.w3.org/TR/")

    assert links == [
        "https://www.w3.org/TR/spec-one",
        "https://www.w3.org/TR/spec-two",
    ]

"""P5 web-crawl tests: bounded traversal, robots, domain, dedupe, write gate.

Uses an injected fake HTTP client (deterministic, no network, no SSRF
obstacle) — the real P4 guard set is covered by test_phase10_web_exec.py.
The crawler must honor max_depth, max_pages, stay_on_domain, obey_robots,
URL dedupe, and the authority write boundary (out_dir must be inside the
authority scope, mirrors the kernel MUTATION rule).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.crawl.crawler import Crawler, CrawlError, domain_of, normalize_url
from jarvis.io.workspace import Authority

# -- Fake guarded HTTP client (mimics HttpClient.fetch result shape) -------
PAGES = {
    "http://seed.test/": {
        "body": "<a href='/a'>A</a> <a href='/b'>B</a> <a href='https://elsewhere.example/x'>X</a>",
    },
    "http://seed.test/a": {"body": "<a href='/a1'>A1</a>"},
    "http://seed.test/b": {"body": "<p>leaf b</p>"},
    "http://seed.test/a1": {"body": "<p>leaf a1</p>"},
    "http://seed.test/robots.txt": {"body": "User-agent: *\nDisallow: /a1\n"},
}


class FakeHttp:
    """Deterministic stand-in: returns canned pages with content_type text/html."""

    def fetch(self, url, authority=None):
        norm = normalize_url(url)
        page = PAGES.get(norm)
        if page is None:
            return {
                "success": False, "url": norm, "final_url": norm,
                "status": 404, "body": "not found", "content_type": "text/html",
                "error": f"404 for {norm}",
            }
        return {
            "success": True, "url": norm, "final_url": norm,
            "status": 200, "body": page["body"], "content_type": "text/html",
        }


@pytest.fixture()
def fake_http():
    return FakeHttp()


@pytest.fixture()
def auth(tmp_path):
    return Authority(
        kind="skill", name="crawl_test", scope=str(tmp_path),
        permissions={"network": "read", "filesystem": "write"},
    )


def test_normalize_url_fragment_dropped():
    assert normalize_url("https://x.com/a?q=1#frag") == "https://x.com/a?q=1"


def test_domain_of():
    assert domain_of("https://sub.example.com:8443/x") == "sub.example.com:8443"


class TestCrawlerGuards:
    def test_depth_limit(self, fake_http, auth, tmp_path):
        out = tmp_path / "semantic"
        r = Crawler(http=fake_http, max_depth=1, max_pages=10).crawl(
            "http://seed.test/", authority=auth, out_dir=out
        )
        # depth 0 (root) + depth 1 (a, b) = 3 pages; a1 at depth 2 must NOT be fetched.
        assert r["fetched"] == 3
        assert all("a1" not in f for f in r["files"])
        assert r["errors"] == []

    def test_domain_lock(self, fake_http, auth, tmp_path):
        out = tmp_path / "semantic"
        r = Crawler(http=fake_http, max_depth=2, max_pages=10, stay_on_domain=True).crawl(
            "http://seed.test/", authority=auth, out_dir=out
        )
        # elsewhere.example is a different domain — must never be fetched.
        assert r["errors"] == []
        assert all("elsewhere" not in f for f in r["files"])

    def test_robots_respected(self, fake_http, auth, tmp_path):
        out = tmp_path / "semantic"
        r = Crawler(http=fake_http, max_depth=2, max_pages=10, robots=True).crawl(
            "http://seed.test/", authority=auth, out_dir=out
        )
        # robots.txt disallows /a1 — a1 must not be fetched.
        assert all("a1" not in f for f in r["files"])
        # but the other discoverable pages are.
        assert r["fetched"] >= 2

    def test_robots_optional(self, fake_http, auth, tmp_path):
        out = tmp_path / "semantic"
        r = Crawler(http=fake_http, max_depth=2, max_pages=10, robots=False).crawl(
            "http://seed.test/", authority=auth, out_dir=out
        )
        # Without robots, /a1 discovered at depth 2 IS fetched.
        assert any("a1" in f for f in r["files"])

    def test_dedupe_visited(self, fake_http, auth, tmp_path):
        out = tmp_path / "semantic"
        r = Crawler(http=fake_http, max_depth=2, max_pages=10).crawl(
            "http://seed.test/", authority=auth, out_dir=out
        )
        assert len(r["files"]) == len(set(r["files"]))

    def test_max_pages(self, fake_http, auth, tmp_path):
        out = tmp_path / "semantic"
        r = Crawler(http=fake_http, max_depth=2, max_pages=1).crawl(
            "http://seed.test/", authority=auth, out_dir=out
        )
        assert r["fetched"] == 1

    def test_write_gate(self, fake_http, auth, tmp_path):
        # Authority scope is OUTSIDE the intended output dir -> the crawl
        # refuses to start (kernel mutation rule); nothing is written.
        out = tmp_path / "semantic"
        bad_auth = Authority(
            kind="skill", name="crawl_bad", scope=str(tmp_path / "elsewhere"),
            permissions={"network": "read", "filesystem": "write"},
        )
        with pytest.raises(CrawlError, match="MUTATION_DENIED"):
            Crawler(http=fake_http, max_depth=1, max_pages=10).crawl(
                "http://seed.test/", authority=bad_auth, out_dir=out
            )
        assert list(out.glob("*.md")) == []

    def test_invalid_seed(self, fake_http, auth, tmp_path):
        with pytest.raises(CrawlError):
            Crawler(http=fake_http).crawl("not-a-url", authority=auth, out_dir=tmp_path)

    def test_pages_written_with_frontmatter(self, fake_http, auth, tmp_path):
        out = tmp_path / "semantic"
        r = Crawler(http=fake_http, max_depth=0, max_pages=1).crawl(
            "http://seed.test/", authority=auth, out_dir=out
        )
        assert r["fetched"] == 1
        files = list(out.glob("*.md"))
        assert len(files) == 1
        text = files[0].read_text(encoding="utf-8")
        assert text.startswith("---")
        assert "source_url:" in text
        assert "depth: 0" in text
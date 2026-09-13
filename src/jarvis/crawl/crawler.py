"""Web crawler (P5) — structured, bounded traversal.

Reuses the guaranteed guard set from ``jarvis.io.http_client`` (scheme,
SSRF IP/port, redirect cap, size cap, authority gate) per fetch, then adds
crawl-level policy: BFS by depth, max-depth, max-pages, same-domain lock,
robots.txt respect, URL deduplication. Output is written through the kernel
write boundary into ``vault/semantic/``.

Everything is deterministic and inspectable: each page is an event-like note
with source URL, fetch time, depth, content type, and the URL hash in the
filename (no lossy transcription).
"""
from __future__ import annotations

import hashlib
import re
import time
from collections import deque
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse

from jarvis.io.workspace import Authority


class LinkExtractor(HTMLParser):
    """Extract ``<a href>`` targets from an HTML body."""

    def __init__(self) -> None:
        super().__init__()
        self.links: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag == "a":
            for attr, value in attrs:
                if attr == "href" and value:
                    self.links.append(value)


class CrawlError(Exception):
    """Raised when a crawl cannot run at all."""


def normalize_url(url: str) -> str:
    """Drop the fragment and normalize scheme/netloc/path for dedupe."""
    try:
        p = urlparse(url)
        return urlunparse((p.scheme, p.netloc, p.path, p.params, p.query, ""))
    except Exception:
        return url


def domain_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def _safe_filename(url: str) -> str:
    """Deterministic filename keyed by URL, kept filesystem-safe."""
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    p = urlparse(url)
    netloc = p.netloc.replace(".", "_").replace(":", "_")
    parts = [x for x in p.path.split("/") if x]
    readable = ""
    if parts and len(parts[0]) <= 20 and re.match(r"^[a-zA-Z0-9_-]+$", parts[0]):
        readable = parts[0]
    stem = f"{netloc}_{readable}".strip("_") if readable else netloc
    if len(stem) > 60:
        stem = stem[:60]
    return f"{stem}_{digest}.md"


class Crawler:
    """Bounded, deterministic web crawler."""

    def __init__(
        self,
        *,
        http=None,  # injected HttpClient for tests
        robots: bool = True,
        max_depth: int = 2,
        max_pages: int = 10,
        stay_on_domain: bool = True,
    ) -> None:
        if max_depth < 0:
            raise CrawlError("max_depth must be >= 0")
        if max_pages <= 0:
            raise CrawlError("max_pages must be > 0")
        self.http = http
        self.robots = robots
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.stay_on_domain = stay_on_domain

    # ------------------------------------------------------------------
    def _fetch(self, client, url: str, authority: Authority):
        result = client.fetch(url, authority=authority)
        if not result.get("success", False):
            raise CrawlError(result.get("error", "fetch failed"))
        return result

    def crawl(
        self,
        seed: str,
        *,
        authority: Authority,
        out_dir: Path,
    ) -> Dict[str, object]:
        """Crawl from ``seed``, writing each page to ``out_dir``.

        Returns an inspection dict (fetched, visited, errors, files).
        """
        from jarvis.io.http_client import HttpClient  # lazy, no network at import

        client = self.http if self.http is not None else HttpClient(max_bytes=1_048_576)

        seed = normalize_url(seed)
        if not domain_of(seed):
            raise CrawlError(f"invalid seed URL: {seed!r}")
        seed_domain = domain_of(seed)

        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # Kernel write-boundary rule: the authority must permit writes here,
        # or every write is refused (no silent out-of-scope mutation).
        if not authority.permits(out_dir):
            raise CrawlError(
                f"MUTATION_DENIED: output dir {out_dir} outside authority scope "
                f"{authority.scope!r}"
            )

        visited: Set[str] = set()
        queue: deque[Tuple[str, int]] = deque([(seed, 0)])
        errors: List[str] = []
        files: List[str] = []
        robots_cache: Dict[str, Tuple[bool, List[Tuple[str, str]]]] = {}
        robots_fetched: Set[str] = set()

        while queue and len(files) < self.max_pages:
            url, depth = queue.popleft()
            url = normalize_url(url)
            if url in visited:
                continue
            visited.add(url)
            if depth > self.max_depth:
                continue
            if self.stay_on_domain and domain_of(url) != seed_domain:
                continue

            # robots.txt check (only when configured); control fetch, not a page.
            if self.robots:
                dom = domain_of(url)
                if dom not in robots_cache:
                    robots_cache[dom] = self._robots_rules(dom, client, authority, scheme=urlparse(url).scheme or "https")
                    robots_fetched.add(dom)
                _, rules = robots_cache[dom]
                if not self._allowed_by_robots(url, rules):
                    continue

            # Fetch with the P4 guard set.
            try:
                result = self._fetch(client, url, authority)
            except Exception as exc:
                errors.append(f"{url}: {exc}")
                continue

            final_url = result.get("final_url", url)
            ct = str(result.get("content_type", "")).lower()
            body = result.get("body", "")

            # Extract same-page links only for HTML.
            if "html" in ct:
                try:
                    parser = LinkExtractor()
                    parser.feed(body if isinstance(body, str) else "")
                except Exception:
                    parser = None
                if parser is not None:
                    for href in parser.links:
                        try:
                            abs_url = normalize_url(urljoin(final_url, href))
                        except Exception:
                            continue
                        if abs_url and abs_url not in visited:
                            queue.append((abs_url, depth + 1))

            # Write page through the kernel write path.
            filename = _safe_filename(final_url)
            rel = f"vault/semantic/{filename}"
            page_text = body if isinstance(body, str) else f"[binary content, {len(body)} bytes]"
            frontmatter = (
                "---\n"
                f"source_url: {final_url}\n"
                f"fetch_timestamp: {int(time.time())}\n"
                f"depth: {depth}\n"
                f"content_type: {ct}\n"
                "---\n\n"
            )
            try:
                (out_dir / filename).write_text(frontmatter + page_text, encoding="utf-8")
            except OSError as exc:
                errors.append(f"{final_url}: write failed: {exc}")
                continue

            files.append(rel)
            # Append discovered same-domain/undiscovered links for the next depth.
            # (Links were enqueued above; nothing else to do.)

        return {
            "fetched": len(files),
            "visited": len(visited),
            "errors": errors,
            "files": files,
            "queue_remaining": len(queue),
            "robots_fetched": len(robots_fetched),
        }

    # ------------------------------------------------------------------
    def _robots_rules(
        self, domain: str, client, authority: Authority, scheme: str = "https"
    ) -> Tuple[bool, List[Tuple[str, str]]]:
        """Best-effort robots.txt fetch; failure => treat as no restrictions."""
        try:
            result = client.fetch(f"{scheme}://{domain}/robots.txt", authority=authority)
        except Exception:
            return False, []
        if not result.get("success", False):
            return False, []
        body = str(result.get("body", ""))
        rules: List[Tuple[str, str]] = []
        agent = "*"
        for line in body.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            low = line.lower()
            if low.startswith("user-agent:"):
                agent = line.split(":", 1)[1].strip()
            elif low.startswith("disallow:"):
                path = line.split(":", 1)[1].strip()
                if path:
                    rules.append((agent, path))
        return True, rules

    @staticmethod
    def _allowed_by_robots(url: str, rules: List[Tuple[str, str]]) -> bool:
        path = urlparse(url).path or "/"
        for agent, disallow in rules:
            if agent in ("*", "JARVIS") and path.startswith(disallow):
                return False
        return True
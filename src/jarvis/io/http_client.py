"""Bounded HTTP reader for the P4 web reader.

Zero-dependency (stdlib only) > no network stack to audit, no supply chain.

Guards (all enforced BEFORE any socket work):
- scheme must be http/https only
- hostname must not be an IPv4 literal (SSRF guard)
- port must not be a blocked port
- size cap on the response body (default 512 KiB)
- redirect limit (default 5) — never follows a redirect whose target
  fails the same guards

Network must be granted explicitly: connect(tool=...) raises PermissionError
unless the caller passes an in-scope ``Authority`` whose ``permissions``
include ``network.read``.
"""
from __future__ import annotations

import gzip
import ipaddress
import socket
import ssl
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.client import HTTPConnection, HTTPSConnection
from typing import Any, Optional

from jarvis.io.workspace import Authority

DEFAULT_MAX_BYTES = 512 * 1024
DEFAULT_REDIRECTS = 5
BLOCKED_PORTS = {21, 22, 23, 25, 53, 110, 135, 139, 445, 1433, 1521, 3306, 5432, 6379}
FETCH_ERRORS = (socket.error, OSError, ssl.SSLError, ValueError)


@dataclass
class FetchResult:
    url: str
    final_url: str
    status: int
    headers: dict[str, str] = field(default_factory=dict)
    body: str = ""
    bytes_read: int = 0
    truncated: bool = False
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "final_url": self.final_url,
            "status": self.status,
            "headers": self.headers,
            "body": self.body,
            "bytes_read": self.bytes_read,
            "truncated": self.truncated,
            "reason": self.reason,
        }


class FetchError(Exception):
    """Typed exception for a blocked/refused web fetch."""

    code = "FETCH_ERROR"

    def __init__(self, message: str, *, url: str = "", code: Optional[str] = None) -> None:
        super().__init__(message)
        self.url = url
        self.message = message
        if code:
            self.code = code


class HttpClient:
    """Bounded http/https reader with SSRF + size + redirect guards."""

    def __init__(
        self,
        max_bytes: int = DEFAULT_MAX_BYTES,
        max_redirects: int = DEFAULT_REDIRECTS,
        timeout: float = 10.0,
    ) -> None:
        self.max_bytes = max_bytes
        self.max_redirects = max_redirects
        self.timeout = timeout

    # ------------------------------------------------------------------
    def fetch(
        self,
        url: str,
        *,
        authority: Optional[Authority] = None,
        method: str = "GET",
        headers: Optional[dict[str, str]] = None,
    ) -> FetchResult:
        """Fetch a URL under the bounce guards.

        Requires an authority whose ``permissions`` dict includes
        ``network.read``. Without it, raises PermissionError.
        """
        self._require_network_read(authority)
        target = self._guard_url(url)
        return self._fetch_with_redirects(target, method, headers or {}, 0)

    # ------------------------------------------------------------ guards
    @staticmethod
    def _require_network_read(authority: Optional[Authority]) -> None:
        if authority is None or not authority.grants("network", "read"):
            raise PermissionError(
                "network.read not granted by authority; pass Authority with "
                "permissions={'network': 'read'}"
            )

    def _guard_url(self, url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url)
        except ValueError as exc:
            raise FetchError(f"unparsable URL: {url}", url=url, code="BAD_URL")
        if parsed.scheme not in ("http", "https"):
            raise FetchError(
                f"scheme '{parsed.scheme}' not allowed (http/https only)",
                url=url, code="SCHEME_BLOCKED",
            )
        try:
            hostname = parsed.hostname
        except ValueError as exc:
            raise FetchError(f"bad hostname: {url}", url=url, code="BAD_URL")
        if not hostname:
            raise FetchError(f"missing hostname: {url}", url=url, code="BAD_URL")
        # SSRF guard: no IPv4 literals (direct IP targets are blocked).
        ip = None
        try:
            ip = ipaddress.ip_address(hostname)
        except ValueError:
            pass
        if ip is not None and ip.version == 4:
            raise FetchError(
                f"IPv4 literal targets are blocked (SSRF guard): {hostname}",
                url=url, code="SSRF_BLOCKED",
            )
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        if port in BLOCKED_PORTS:
            raise FetchError(
                f"port {port} is blocked, refused: {url}",
                url=url, code="PORT_BLOCKED",
            )
        return url

    # ------------------------------------------------------------ engine
    def _fetch_with_redirects(
        self,
        url: str,
        method: str,
        headers: dict[str, str],
        depth: int,
    ) -> FetchResult:
        if depth > self.max_redirects:
            raise FetchError("too many redirects", url=url, code="TOO_MANY_REDIRECTS")
        target = self._guard_url(url)
        parsed = urllib.parse.urlparse(target)
        https = parsed.scheme == "https"
        host = parsed.hostname
        port = parsed.port or (443 if https else 80)

        if host is None:
            raise FetchError(f"missing hostname: {target}", url=target, code="BAD_URL")
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query

        req_headers = {
            "User-Agent": "JARVIS/0.2 (bounded web reader)",
            "Accept": "text/html,text/markdown,text/plain,*/*;q=0.5",
            "Accept-Encoding": "gzip",
        }
        req_headers.update(headers)

        conn: HTTPConnection | HTTPSConnection
        try:
            if https:
                ctx = ssl.create_default_context()
                conn = HTTPSConnection(host, port=port, timeout=self.timeout, context=ctx)
            else:
                conn = HTTPConnection(host, port=port, timeout=self.timeout)
            conn.request(method, path, headers=req_headers)
            resp = conn.getresponse()
        except FETCH_ERRORS as exc:
            raise FetchError(f"connection failed: {exc}", url=target, code="CONNECT_FAILED")
        except Exception as exc:  # noqa: BLE001 — defensive
            raise FetchError(f"unexpected fetch error: {exc}", url=target)

        status = resp.status
        response_headers = {k.lower(): v for k, v in resp.getheaders()}

        if status in (301, 302, 303, 307, 308):
            loc = response_headers.get("location")
            conn.close()
            if not loc:
                raise FetchError(f"redirect without Location: {target}", url=target)
            new_url = urllib.parse.urljoin(target, loc)
            new_url = self._guard_url(new_url)
            return self._fetch_with_redirects(new_url, method, headers, depth + 1)

        raw = resp.read(self.max_bytes + 1)
        conn.close()
        truncated = len(raw) > self.max_bytes
        body = raw[: self.max_bytes]

        encoding = response_headers.get("content-encoding", "")
        if "gzip" in encoding:
            try:
                body = gzip.decompress(body)
            except (OSError, EOFError):
                pass  # fall through to raw if gzip failed

        try:
            text = body.decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            text = body.decode("latin-1", errors="replace")

        return FetchResult(
            url=url,
            final_url=target,
            status=status,
            headers=dict(response_headers),
            body=text,
            bytes_read=len(body),
            truncated=truncated,
            reason=resp.reason or "",
        )
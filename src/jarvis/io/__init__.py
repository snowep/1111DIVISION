"""io: workspace access + bounded network read (http client).

Imports stay lazy so modules can use these helpers without circulars.
"""
from __future__ import annotations

from jarvis.io.workspace import Authority, SafeIO, WorkspaceResolver


def http_client() -> "HttpClient":
    """Lazily build the bounded HTTP reader (dependency-free)."""
    from jarvis.io.http_client import HttpClient
    return HttpClient()


__all__ = ["Authority", "SafeIO", "WorkspaceResolver", "http_client"]
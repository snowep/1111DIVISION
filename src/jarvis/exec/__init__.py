"""exec: safe, guarded shell execution (P3b) — blocklist-first and auditable."""
from jarvis.exec.safe import ExecResult, safe_exec

__all__ = ["ExecResult", "safe_exec"]
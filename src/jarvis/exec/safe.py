"""Safe shell execution with workspace pinning (P3b).

Blocklist-first, output-capped, timeout-bounded, cwd confined to the
workspace. Returns a structured dict (success, returncode, stdout, stderr,
warnings). Execution is NEVER silent: every run is returned to the caller
for audit.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from jarvis.io.workspace import Authority

DEFAULT_TIMEOUT = 30
MAX_OUTPUT = 8000

# Blocklist prefixes (case-insensitive). Anything starting with one of these
# is refused before touching the shell.
BLOCKLIST = [
    "rm ", "del ", "format ", "fdisk ", "mkfs.", "dd if=", "> /dev/sd",
    "shutdown", "reboot", "init 0", "init 6", "halt", "poweroff",
    "mv /", "cp /", "chmod -R", "chown -R", "killall", "pkill", "sudo ",
    "su ", "visudo", "crontab -r", "> /etc/", "mv /etc/", "rm -rf",
]


@dataclass
class ExecResult:
    success: bool
    command: str
    returncode: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    cwd: str = ""
    timeout: int = DEFAULT_TIMEOUT
    warnings: list[str] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "command": self.command,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "cwd": self.cwd,
            "timeout": self.timeout,
            "warnings": self.warnings,
            "error": self.error,
        }


def _authorize(authority: Optional[Authority]) -> None:
    if authority is None or not authority.grants("terminal", "execute"):
        raise PermissionError(
            "terminal.execute not granted; pass Authority with "
            "permissions={'terminal': 'execute'}"
        )


def _is_blocked(command: str) -> Optional[str]:
    low = command.lower().strip()
    for blocked in BLOCKLIST:
        if low.startswith(blocked):
            return blocked
    return None


def safe_exec(
    command: str,
    *,
    cwd: Optional[Path] = None,
    timeout: int = DEFAULT_TIMEOUT,
    workspace_root: Optional[Path] = None,
    authority: Optional[Authority] = None,
) -> ExecResult:
    """Run a command inside the workspace with guards.

    ``workspace_root`` defaults to cwd. The command must not contain a
    blocked prefix; cwd must be inside the workspace; output is capped.
    """
    _authorize(authority)
    ws = (workspace_root or cwd or Path.cwd()).resolve()
    workdir = (cwd or ws).resolve()
    try:
        workdir.relative_to(ws)
    except ValueError:
        return ExecResult(
            success=False, command=command, cwd=str(workdir),
            error=f"cwd {workdir} outside workspace {ws}", warnings=["CWD_ESCAPE"],
        )

    blocked = _is_blocked(command)
    if blocked:
        return ExecResult(
            success=False, command=command, cwd=str(workdir),
            error=f"blocked command prefix: {blocked!r}", warnings=["BLOCKED"],
        )

    try:
        proc = subprocess.run(
            command, shell=True, cwd=str(workdir), timeout=timeout,
            capture_output=True, text=True,
        )
    except subprocess.TimeoutExpired:
        return ExecResult(
            success=False, command=command, cwd=str(workdir),
            timeout=timeout, error=f"timed out after {timeout}s", warnings=["TIMEOUT"],
        )
    except Exception as exc:  # noqa: BLE001
        return ExecResult(
            success=False, command=command, cwd=str(workdir),
            error=f"exec failed: {exc}", warnings=["EXEC_ERROR"],
        )

    stdout = proc.stdout
    stderr = proc.stderr
    warnings: list[str] = []
    if len(stdout) > MAX_OUTPUT:
        stdout = stdout[:MAX_OUTPUT] + "\n...(output truncated)"
        warnings.append("STDOUT_TRUNCATED")
    if len(stderr) > MAX_OUTPUT:
        stderr = stderr[:MAX_OUTPUT] + "\n...(output truncated)"
        warnings.append("STDERR_TRUNCATED")
    return ExecResult(
        success=proc.returncode == 0,
        command=command,
        returncode=proc.returncode,
        stdout=stdout,
        stderr=stderr,
        cwd=str(workdir),
        timeout=timeout,
        warnings=warnings,
        error="" if proc.returncode == 0 else f"exit code {proc.returncode}",
    )
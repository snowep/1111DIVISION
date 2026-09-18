"""
ORION Workspace Tools

Actual implementations of tools that the ORION executor can use.
Each tool integrates with the permissions engine for authorization.
"""

from __future__ import annotations
import json
import os
import subprocess
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from datetime import datetime

from .permissions import PermissionsEngine, ToolRegistry, PermissionLevel, ApprovalRequest


@dataclass
class ToolResult:
    """Result of a tool execution."""
    success: bool
    output: Any
    error: str | None = None
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class WorkspaceTools:
    """
    Collection of workspace tools with permission integration.
    """
    
    def __init__(self, root: Path, permissions: PermissionsEngine, registry: ToolRegistry):
        self.root = root
        self.permissions = permissions
        self.registry = registry
        self._pending_approval: Optional[ApprovalRequest] = None
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve a path relative to workspace root."""
        p = Path(path)
        if not p.is_absolute():
            p = self.root / p
        return p.resolve()
    
    def _check_permission(self, tool_name: str, args: dict = None) -> PermissionLevel:
        """Check permission for a tool."""
        return self.registry.check_permission(tool_name, args)
    
    def _request_approval(self, tool_name: str, args: dict = None) -> Optional[ApprovalRequest]:
        """Request approval if needed."""
        return self.registry.request_tool_approval(tool_name, args)
    
    # ==================== FILE TOOLS ====================
    
    def read_file(self, path: str, start_line: int = None, end_line: int = None) -> ToolResult:
        """Read a file from the filesystem."""
        perm = self._check_permission("read_file", {"path": path})
        if perm == PermissionLevel.CONFIRM:
            return ToolResult(False, None, "Requires confirmation", 
                            {"approval_request": self._request_approval("read_file", {"path": path}).__dict__})
        elif perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        try:
            full_path = self._resolve_path(path)
            if not full_path.exists():
                return ToolResult(False, None, f"File not found: {path}")
            
            content = full_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            
            if start_line is not None or end_line is not None:
                start = max(0, (start_line or 1) - 1)
                end = min(len(lines), end_line or len(lines))
                content = "\n".join(lines[start:end])
            
            return ToolResult(True, content, metadata={"lines": len(lines), "path": str(full_path)})
        except Exception as e:
            return ToolResult(False, None, str(e))
    
    def write_file(self, path: str, content: str) -> ToolResult:
        """Write content to a file."""
        perm = self._check_permission("write_file", {"path": path})
        if perm == PermissionLevel.CONFIRM:
            return ToolResult(False, None, "Requires confirmation",
                            {"approval_request": self._request_approval("write_file", {"path": path}).__dict__})
        elif perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        try:
            full_path = self._resolve_path(path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")
            return ToolResult(True, f"Written {len(content)} bytes to {path}", 
                            metadata={"path": str(full_path), "size": len(content)})
        except Exception as e:
            return ToolResult(False, None, str(e))
    
    def edit_file(self, path: str, find: str, replace: str, allow_multiple: bool = False) -> ToolResult:
        """Edit a file using find/replace."""
        perm = self._check_permission("edit_file", {"path": path})
        if perm == PermissionLevel.CONFIRM:
            return ToolResult(False, None, "Requires confirmation",
                            {"approval_request": self._request_approval("edit_file", {"path": path}).__dict__})
        elif perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        try:
            full_path = self._resolve_path(path)
            if not full_path.exists():
                return ToolResult(False, None, f"File not found: {path}")
            
            content = full_path.read_text(encoding="utf-8")
            
            if allow_multiple:
                new_content = content.replace(find, replace)
                count = content.count(find)
            else:
                if find not in content:
                    return ToolResult(False, None, "Find string not found in file")
                if content.count(find) > 1:
                    return ToolResult(False, None, "Multiple matches found; use allow_multiple=true")
                new_content = content.replace(find, replace)
                count = 1
            
            full_path.write_text(new_content, encoding="utf-8")
            return ToolResult(True, f"Replaced {count} occurrence(s)", 
                            metadata={"path": str(full_path), "replacements": count})
        except Exception as e:
            return ToolResult(False, None, str(e))
    
    def delete_file(self, path: str) -> ToolResult:
        """Delete a file."""
        perm = self._check_permission("delete_file", {"path": path})
        if perm == PermissionLevel.CONFIRM:
            return ToolResult(False, None, "Requires confirmation",
                            {"approval_request": self._request_approval("delete_file", {"path": path}).__dict__})
        elif perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        try:
            full_path = self._resolve_path(path)
            if not full_path.exists():
                return ToolResult(False, None, f"File not found: {path}")
            
            if full_path.is_dir():
                shutil.rmtree(full_path)
            else:
                full_path.unlink()
            
            return ToolResult(True, f"Deleted {path}", metadata={"path": str(full_path)})
        except Exception as e:
            return ToolResult(False, None, str(e))
    
    def list_files(self, path: str = ".") -> ToolResult:
        """List directory contents."""
        perm = self._check_permission("list_files", {"path": path})
        if perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        try:
            full_path = self._resolve_path(path)
            if not full_path.exists():
                return ToolResult(False, None, f"Directory not found: {path}")
            
            entries = []
            for item in sorted(full_path.iterdir()):
                entries.append({
                    "name": item.name + ("/" if item.is_dir() else ""),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                })
            
            return ToolResult(True, entries, metadata={"path": str(full_path), "count": len(entries)})
        except Exception as e:
            return ToolResult(False, None, str(e))
    
    def glob_search(self, pattern: str, path: str = ".") -> ToolResult:
        """Find files by glob pattern."""
        perm = self._check_permission("glob_search", {"pattern": pattern, "path": path})
        if perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        try:
            full_path = self._resolve_path(path)
            matches = []
            for item in full_path.rglob(pattern):
                if ".git" in item.parts:
                    continue
                rel = item.relative_to(self.root)
                matches.append({
                    "path": str(rel),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            return ToolResult(True, sorted(matches, key=lambda x: x["path"]), 
                            metadata={"pattern": pattern, "count": len(matches)})
        except Exception as e:
            return ToolResult(False, None, str(e))
    
    # ==================== CODE TOOLS ====================
    
    def run_tests(self, command: str = None, path: str = ".") -> ToolResult:
        """Run test suite."""
        cmd = command or self._detect_test_command(path)
        perm = self._check_permission("run_tests", {"command": cmd, "path": path})
        if perm == PermissionLevel.CONFIRM:
            return ToolResult(False, None, "Requires confirmation",
                            {"approval_request": self._request_approval("run_tests", {"command": cmd}).__dict__})
        elif perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        try:
            full_path = self._resolve_path(path)
            result = subprocess.run(
                cmd, shell=True, cwd=full_path,
                capture_output=True, text=True, timeout=120
            )
            return ToolResult(
                result.returncode == 0,
                {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode},
                None if result.returncode == 0 else result.stderr,
                metadata={"command": cmd, "duration": "N/A"}
            )
        except subprocess.TimeoutExpired:
            return ToolResult(False, None, "Test timeout (120s)")
        except Exception as e:
            return ToolResult(False, None, str(e))
    
    def lint_code(self, command: str = None, path: str = ".") -> ToolResult:
        """Run linter/formatter."""
        cmd = command or self._detect_lint_command(path)
        perm = self._check_permission("lint_code", {"command": cmd, "path": path})
        if perm == PermissionLevel.CONFIRM:
            return ToolResult(False, None, "Requires confirmation",
                            {"approval_request": self._request_approval("lint_code", {"command": cmd}).__dict__})
        elif perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        try:
            full_path = self._resolve_path(path)
            result = subprocess.run(
                cmd, shell=True, cwd=full_path,
                capture_output=True, text=True, timeout=60
            )
            return ToolResult(
                result.returncode == 0,
                {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode},
                None if result.returncode == 0 else result.stderr,
                metadata={"command": cmd}
            )
        except Exception as e:
            return ToolResult(False, None, str(e))
    
    def build_project(self, command: str = None, path: str = ".") -> ToolResult:
        """Build the project."""
        cmd = command or self._detect_build_command(path)
        perm = self._check_permission("build_project", {"command": cmd, "path": path})
        if perm == PermissionLevel.CONFIRM:
            return ToolResult(False, None, "Requires confirmation",
                            {"approval_request": self._request_approval("build_project", {"command": cmd}).__dict__})
        elif perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        try:
            full_path = self._resolve_path(path)
            result = subprocess.run(
                cmd, shell=True, cwd=full_path,
                capture_output=True, text=True, timeout=180
            )
            return ToolResult(
                result.returncode == 0,
                {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode},
                None if result.returncode == 0 else result.stderr,
                metadata={"command": cmd}
            )
        except Exception as e:
            return ToolResult(False, None, str(e))
    
    def deploy(self, target: str, command: str) -> ToolResult:
        """Deploy to production (requires confirmation)."""
        perm = self._check_permission("deploy", {"target": target, "command": command})
        if perm == PermissionLevel.CONFIRM:
            return ToolResult(False, None, "Requires confirmation",
                            {"approval_request": self._request_approval("deploy", {"target": target, "command": command}).__dict__})
        elif perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        try:
            result = subprocess.run(
                command, shell=True, cwd=self.root,
                capture_output=True, text=True, timeout=300
            )
            return ToolResult(
                result.returncode == 0,
                {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode},
                None if result.returncode == 0 else result.stderr,
                metadata={"target": target, "command": command}
            )
        except Exception as e:
            return ToolResult(False, None, str(e))
    
    # ==================== TERMINAL TOOLS ====================
    
    def run_command(self, command: str, cwd: str = ".", wait: str = "30") -> ToolResult:
        """Execute a shell command."""
        perm = self._check_permission("run_command", {"command": command, "cwd": cwd})
        if perm == PermissionLevel.CONFIRM:
            return ToolResult(False, None, "Requires confirmation",
                            {"approval_request": self._request_approval("run_command", {"command": command, "cwd": cwd}).__dict__})
        elif perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        try:
            full_cwd = self._resolve_path(cwd)
            timeout = int(wait) if wait else 30
            result = subprocess.run(
                command, shell=True, cwd=full_cwd,
                capture_output=True, text=True, timeout=timeout
            )
            return ToolResult(
                result.returncode == 0,
                {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode},
                None if result.returncode == 0 else result.stderr,
                metadata={"command": command, "cwd": str(full_cwd)}
            )
        except subprocess.TimeoutExpired:
            return ToolResult(False, None, f"Command timeout ({wait}s)")
        except Exception as e:
            return ToolResult(False, None, str(e))
    
    def run_background(self, command: str, cwd: str = ".") -> ToolResult:
        """Start a background process."""
        perm = self._check_permission("run_background", {"command": command, "cwd": cwd})
        if perm == PermissionLevel.CONFIRM:
            return ToolResult(False, None, "Requires confirmation",
                            {"approval_request": self._request_approval("run_background", {"command": command, "cwd": cwd}).__dict__})
        elif perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        try:
            full_cwd = self._resolve_path(cwd)
            proc = subprocess.Popen(
                command, shell=True, cwd=full_cwd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            return ToolResult(True, {"pid": proc.pid, "command": command},
                            metadata={"pid": proc.pid, "cwd": str(full_cwd)})
        except Exception as e:
            return ToolResult(False, None, str(e))
    
    # ==================== GIT TOOLS ====================
    
    def git_status(self) -> ToolResult:
        """Get git status."""
        perm = self._check_permission("git_status", {})
        if perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.root, capture_output=True, text=True, timeout=10
            )
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.root, capture_output=True, text=True, timeout=5
            )
            
            changes = result.stdout.strip().split("\n") if result.stdout.strip() else []
            return ToolResult(True, {
                "clean": result.stdout.strip() == "",
                "changes": changes,
                "branch": branch_result.stdout.strip()
            })
        except Exception as e:
            return ToolResult(False, None, str(e))
    
    def git_commit(self, message: str, files: list[str] = None) -> ToolResult:
        """Create a git commit."""
        perm = self._check_permission("git_commit", {"message": message, "files": files})
        if perm == PermissionLevel.CONFIRM:
            return ToolResult(False, None, "Requires confirmation",
                            {"approval_request": self._request_approval("git_commit", {"message": message}).__dict__})
        elif perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        try:
            if files:
                subprocess.run(["git", "add"] + files, cwd=self.root, check=True, capture_output=True)
            else:
                subprocess.run(["git", "add", "-A"], cwd=self.root, check=True, capture_output=True)
            
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.root, capture_output=True, text=True, timeout=30
            )
            return ToolResult(
                result.returncode == 0,
                {"stdout": result.stdout, "stderr": result.stderr},
                None if result.returncode == 0 else result.stderr,
                metadata={"message": message}
            )
        except Exception as e:
            return ToolResult(False, None, str(e))
    
    def git_push(self, remote: str = "origin", branch: str = None, force: bool = False) -> ToolResult:
        """Push to remote."""
        args = {"remote": remote, "branch": branch, "force": force}
        perm = self._check_permission("git_push", args)
        if perm == PermissionLevel.CONFIRM:
            return ToolResult(False, None, "Requires confirmation",
                            {"approval_request": self._request_approval("git_push", args).__dict__})
        elif perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        try:
            cmd = ["git", "push", remote]
            if branch:
                cmd.append(branch)
            if force:
                cmd.append("--force")
            
            result = subprocess.run(cmd, cwd=self.root, capture_output=True, text=True, timeout=60)
            return ToolResult(
                result.returncode == 0,
                {"stdout": result.stdout, "stderr": result.stderr},
                None if result.returncode == 0 else result.stderr,
                metadata=args
            )
        except Exception as e:
            return ToolResult(False, None, str(e))
    
    def git_branch(self, name: str, delete: bool = False) -> ToolResult:
        """Create or delete a branch."""
        args = {"name": name, "delete": delete}
        perm = self._check_permission("git_branch", args)
        if perm == PermissionLevel.CONFIRM:
            return ToolResult(False, None, "Requires confirmation",
                            {"approval_request": self._request_approval("git_branch", args).__dict__})
        elif perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        try:
            if delete:
                result = subprocess.run(
                    ["git", "branch", "-D", name],
                    cwd=self.root, capture_output=True, text=True, timeout=10
                )
            else:
                result = subprocess.run(
                    ["git", "checkout", "-b", name],
                    cwd=self.root, capture_output=True, text=True, timeout=10
                )
            return ToolResult(
                result.returncode == 0,
                {"stdout": result.stdout, "stderr": result.stderr},
                None if result.returncode == 0 else result.stderr,
                metadata=args
            )
        except Exception as e:
            return ToolResult(False, None, str(e))
    
    # ==================== WEB TOOLS ====================
    
    def web_search(self, query: str, count: int = 5) -> ToolResult:
        """Search the web (placeholder - would integrate with search API)."""
        perm = self._check_permission("web_search", {"query": query})
        if perm == PermissionLevel.CONFIRM:
            return ToolResult(False, None, "Requires confirmation",
                            {"approval_request": self._request_approval("web_search", {"query": query}).__dict__})
        elif perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        # Placeholder - actual implementation would call search API
        return ToolResult(True, {"query": query, "results": [], "note": "Web search not implemented - placeholder"},
                        metadata={"query": query, "count": count})
    
    def web_fetch(self, url: str) -> ToolResult:
        """Fetch a web page (placeholder)."""
        perm = self._check_permission("web_fetch", {"url": url})
        if perm == PermissionLevel.CONFIRM:
            return ToolResult(False, None, "Requires confirmation",
                            {"approval_request": self._request_approval("web_fetch", {"url": url}).__dict__})
        elif perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        # Placeholder
        return ToolResult(True, {"url": url, "content": "", "note": "Web fetch not implemented - placeholder"},
                        metadata={"url": url})
    
    # ==================== API TOOLS ====================
    
    def api_get(self, url: str, headers: dict = None) -> ToolResult:
        """GET request to API (placeholder)."""
        perm = self._check_permission("api_get", {"url": url, "method": "GET"})
        if perm == PermissionLevel.CONFIRM:
            return ToolResult(False, None, "Requires confirmation",
                            {"approval_request": self._request_approval("api_get", {"url": url}).__dict__})
        elif perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        return ToolResult(True, {"url": url, "note": "API GET not implemented - placeholder"}, metadata={"url": url})
    
    def api_post(self, url: str, data: dict, headers: dict = None) -> ToolResult:
        """POST request to API (placeholder - requires confirmation)."""
        perm = self._check_permission("api_post", {"url": url, "method": "POST"})
        if perm == PermissionLevel.CONFIRM:
            return ToolResult(False, None, "Requires confirmation",
                            {"approval_request": self._request_approval("api_post", {"url": url}).__dict__})
        elif perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        return ToolResult(True, {"url": url, "note": "API POST not implemented - placeholder"}, metadata={"url": url})
    
    def api_delete(self, url: str, headers: dict = None) -> ToolResult:
        """DELETE request to API (placeholder - requires confirmation)."""
        perm = self._check_permission("api_delete", {"url": url, "method": "DELETE"})
        if perm == PermissionLevel.CONFIRM:
            return ToolResult(False, None, "Requires confirmation",
                            {"approval_request": self._request_approval("api_delete", {"url": url}).__dict__})
        elif perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        return ToolResult(True, {"url": url, "note": "API DELETE not implemented - placeholder"}, metadata={"url": url})
    
    # ==================== DATABASE TOOLS ====================
    
    def db_query(self, query: str, params: list = None) -> ToolResult:
        """Execute SELECT query (placeholder)."""
        perm = self._check_permission("db_query", {"query": query})
        if perm == PermissionLevel.CONFIRM:
            return ToolResult(False, None, "Requires confirmation",
                            {"approval_request": self._request_approval("db_query", {"query": query}).__dict__})
        elif perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        return ToolResult(True, {"query": query, "note": "Database query not implemented - placeholder"}, metadata={})
    
    def db_execute(self, query: str, params: list = None) -> ToolResult:
        """Execute INSERT/UPDATE/CREATE (placeholder - requires confirmation)."""
        perm = self._check_permission("db_execute", {"query": query})
        if perm == PermissionLevel.CONFIRM:
            return ToolResult(False, None, "Requires confirmation",
                            {"approval_request": self._request_approval("db_execute", {"query": query}).__dict__})
        elif perm == PermissionLevel.DENY:
            return ToolResult(False, None, "Permission denied")
        
        return ToolResult(True, {"query": query, "note": "Database execute not implemented - placeholder"}, metadata={})
    
    # ==================== HELPERS ====================
    
    def _detect_test_command(self, path: str) -> str:
        """Detect test command for project."""
        full_path = self._resolve_path(path)
        if (full_path / "package.json").exists():
            return "npm test"
        elif (full_path / "pyproject.toml").exists() or (full_path / "pytest.ini").exists():
            return "python -m pytest"
        elif (full_path / "Cargo.toml").exists():
            return "cargo test"
        elif (full_path / "go.mod").exists():
            return "go test ./..."
        return "python -m pytest"
    
    def _detect_lint_command(self, path: str) -> str:
        """Detect lint command for project."""
        full_path = self._resolve_path(path)
        if (full_path / "package.json").exists():
            return "npm run lint"
        elif (full_path / "pyproject.toml").exists():
            return "ruff check ."
        return "echo 'No linter detected'"
    
    def _detect_build_command(self, path: str) -> str:
        """Detect build command for project."""
        full_path = self._resolve_path(path)
        if (full_path / "package.json").exists():
            return "npm run build"
        elif (full_path / "pyproject.toml").exists():
            return "python -m build"
        elif (full_path / "Cargo.toml").exists():
            return "cargo build --release"
        return "echo 'No build command detected'"


class ExecutorWithTools:
    """
    Enhanced Executor that uses WorkspaceTools for actual execution.
    Integrates with permissions engine for authorization.
    """
    
    def __init__(self, root: Path, permissions: PermissionsEngine, registry: ToolRegistry):
        self.root = root
        self.tools = WorkspaceTools(root, permissions, registry)
        self.permissions = permissions
        self.registry = registry
    
    def execute_step(self, step: str, context: dict) -> tuple[bool, Any]:
        """Execute a plan step using available tools."""
        step_lower = step.lower()
        
        def has_word(text: str, *words: str) -> bool:
            return any(f" {w} " in f" {text} " or text.startswith(f"{w} ") or text.endswith(f" {w}") for w in words)
        
        # File operations
        if has_word(step_lower, "create") and has_word(step_lower, "file", "directory", "director", "structure"):
            return self._handle_create(step, context)
        elif has_word(step_lower, "write") and not has_word(step_lower, "commit"):
            return self._handle_write(step, context)
        elif has_word(step_lower, "edit") or has_word(step_lower, "modify"):
            return self._handle_edit(step, context)
        elif has_word(step_lower, "delete") and not has_word(step_lower, "branch", "tag"):
            return self._handle_delete(step, context)
        elif has_word(step_lower, "inspect"):
            return self._handle_inspect(step, context)
        elif has_word(step_lower, "read"):
            return self._handle_read(step, context)
        elif has_word(step_lower, "list") or has_word(step_lower, "search") or has_word(step_lower, "find"):
            return self._handle_search(step, context)
        
        # Code operations
        elif has_word(step_lower, "test") or has_word(step_lower, "pytest"):
            return self._handle_test(step, context)
        elif has_word(step_lower, "lint") or has_word(step_lower, "format") or has_word(step_lower, "typecheck"):
            return self._handle_lint(step, context)
        elif has_word(step_lower, "build") or has_word(step_lower, "compile"):
            return self._handle_build(step, context)
        elif has_word(step_lower, "deploy"):
            return self._handle_deploy(step, context)
        
        # Terminal operations
        elif has_word(step_lower, "run") and has_word(step_lower, "command"):
            return self._handle_command(step, context)
        elif has_word(step_lower, "execute necessary actions"):
            return True, {"action": "execute", "step": step, "status": "planned - generic execution step"}
        elif has_word(step_lower, "execute") and not has_word(step_lower, "test", "build", "deploy"):
            return self._handle_command(step, context)
        
        # Git operations
        elif has_word(step_lower, "commit") or has_word(step_lower, "push") or has_word(step_lower, "branch"):
            return self._handle_git(step, context)
        elif has_word(step_lower, "git") or has_word(step_lower, "status") or has_word(step_lower, "diff"):
            return self._handle_git(step, context)
        
        # Analysis/Verification
        elif has_word(step_lower, "verify") or has_word(step_lower, "check"):
            return self._handle_verify(step, context)
        elif has_word(step_lower, "identify") or has_word(step_lower, "scope") or has_word(step_lower, "target"):
            return self._handle_identify(step, context)
        elif has_word(step_lower, "summarize") or has_word(step_lower, "report"):
            return self._handle_summarize(step, context)
        elif has_word(step_lower, "understand"):
            return self._handle_understand(step, context)
        elif has_word(step_lower, "critique"):
            return self._handle_critique(step, context)
        elif has_word(step_lower, "perform"):
            return self._handle_perform(step, context)
        elif has_word(step_lower, "reproduce") or has_word(step_lower, "locate"):
            return self._handle_reproduce(step, context)
        elif has_word(step_lower, "implement") or has_word(step_lower, "fix") or has_word(step_lower, "repair") or has_word(step_lower, "correct"):
            return self._handle_implement(step, context)
        
        return True, {"acknowledged": step, "note": "Step logged for manual execution"}
    
    # Handler methods
    def _handle_create(self, step: str, context: dict) -> tuple[bool, Any]:
        return True, {"action": "create", "step": step, "status": "planned - use write_file tool"}
    
    def _handle_inspect(self, step: str, context: dict) -> tuple[bool, Any]:
        # Actually inspect using the inspector
        from .core import WorkspaceInspector
        inspector = WorkspaceInspector(self.root)
        inspection = inspector.inspect()
        return True, {"action": "inspect", "step": step, "inspection": inspection}
    
    def _handle_write(self, step: str, context: dict) -> tuple[bool, Any]:
        return True, {"action": "write", "step": step, "status": "planned - use write_file tool"}
    
    def _handle_edit(self, step: str, context: dict) -> tuple[bool, Any]:
        return True, {"action": "edit", "step": step, "status": "planned - use edit_file tool"}
    
    def _handle_delete(self, step: str, context: dict) -> tuple[bool, Any]:
        return True, {"action": "delete", "step": step, "status": "planned - use delete_file tool"}
    
    def _handle_read(self, step: str, context: dict) -> tuple[bool, Any]:
        # Try to extract path from step
        import re
        paths = re.findall(r'[\w\./\\-]+\.\w+', step)
        if paths:
            result = self.tools.read_file(paths[0])
            return result.success, {"action": "read", "step": step, "result": result.output, "error": result.error}
        return True, {"action": "read", "step": step, "status": "planned - specify file path"}
    
    def _handle_search(self, step: str, context: dict) -> tuple[bool, Any]:
        import re
        patterns = re.findall(r'[\w\./\\-*]+\.\w+', step)
        if patterns:
            result = self.tools.glob_search(patterns[0])
            return result.success, {"action": "search", "step": step, "result": result.output}
        return True, {"action": "search", "step": step, "status": "planned - specify pattern"}
    
    def _handle_test(self, step: str, context: dict) -> tuple[bool, Any]:
        result = self.tools.run_tests()
        return result.success, {"action": "test", "step": step, "result": result.output, "error": result.error}
    
    def _handle_lint(self, step: str, context: dict) -> tuple[bool, Any]:
        result = self.tools.lint_code()
        return result.success, {"action": "lint", "step": step, "result": result.output, "error": result.error}
    
    def _handle_build(self, step: str, context: dict) -> tuple[bool, Any]:
        result = self.tools.build_project()
        return result.success, {"action": "build", "step": step, "result": result.output, "error": result.error}
    
    def _handle_deploy(self, step: str, context: dict) -> tuple[bool, Any]:
        return True, {"action": "deploy", "step": step, "status": "planned - use deploy tool with target"}
    
    def _handle_command(self, step: str, context: dict) -> tuple[bool, Any]:
        # Try to extract command
        import re
        # Look for quoted command or after "run"/"execute"
        match = re.search(r'(?:run|execute)\s+["\']?([^"\']+)["\']?', step, re.IGNORECASE)
        if match:
            cmd = match.group(1)
            result = self.tools.run_command(cmd)
            return result.success, {"action": "command", "step": step, "result": result.output, "error": result.error}
        return True, {"action": "command", "step": step, "status": "planned - specify command"}
    
    def _handle_git(self, step: str, context: dict) -> tuple[bool, Any]:
        step_lower = step.lower()
        if "status" in step_lower:
            result = self.tools.git_status()
            return result.success, {"action": "git_status", "step": step, "result": result.output}
        elif "commit" in step_lower:
            return True, {"action": "git_commit", "step": step, "status": "planned - use git_commit tool with message"}
        elif "push" in step_lower:
            return True, {"action": "git_push", "step": step, "status": "planned - use git_push tool"}
        elif "branch" in step_lower:
            return True, {"action": "git_branch", "step": step, "status": "planned - use git_branch tool"}
        return True, {"action": "git", "step": step, "status": "planned"}
    
    def _handle_verify(self, step: str, context: dict) -> tuple[bool, Any]:
        return True, {"action": "verify", "step": step, "status": "planned"}
    
    def _handle_identify(self, step: str, context: dict) -> tuple[bool, Any]:
        inspection = context.get("inspection", {})
        key_files = inspection.get("key_files", [])
        structure = inspection.get("structure", {})
        return True, {
            "action": "identify",
            "step": step,
            "scope": "workspace root and .agent directory",
            "targets_found": len(key_files),
            "key_files": key_files[:20],
            "structure_keys": list(structure.keys())
        }
    
    def _handle_summarize(self, step: str, context: dict) -> tuple[bool, Any]:
        inspection = context.get("inspection", {})
        key_files = inspection.get("key_files", [])
        structure = inspection.get("structure", {})
        git_status = inspection.get("git_status", {})
        
        summary = {
            "workspace_root": inspection.get("root"),
            "total_key_files": len(key_files),
            "top_level_dirs": list(structure.keys()),
            "git_branch": git_status.get("branch"),
            "git_clean": git_status.get("clean"),
            "key_files_by_type": {}
        }
        
        for f in key_files:
            ext = f.split(".")[-1] if "." in f else "no_ext"
            summary["key_files_by_type"][ext] = summary["key_files_by_type"].get(ext, 0) + 1
        
        return True, {"action": "summarize", "step": step, "summary": summary}
    
    def _handle_understand(self, step: str, context: dict) -> tuple[bool, Any]:
        understanding = context.get("understanding", {})
        return True, {
            "action": "understand",
            "step": step,
            "objective": understanding.get("objective"),
            "keywords": understanding.get("keywords"),
            "complexity": understanding.get("complexity"),
            "requires_tools": understanding.get("requires_tools")
        }
    
    def _handle_critique(self, step: str, context: dict) -> tuple[bool, Any]:
        return True, {"action": "critique", "step": step, "status": "planned"}
    
    def _handle_perform(self, step: str, context: dict) -> tuple[bool, Any]:
        return True, {"action": "perform", "step": step, "status": "planned"}
    
    def _handle_reproduce(self, step: str, context: dict) -> tuple[bool, Any]:
        return True, {"action": "reproduce", "step": step, "status": "planned"}
    
    def _handle_implement(self, step: str, context: dict) -> tuple[bool, Any]:
        return True, {"action": "implement", "step": step, "status": "planned"}
"""
ORION Permissions System

Controls access to tools and operations with tiered authorization.
Implements the JARVIS-like autonomy model: autonomous by default, confirmation for risky operations.
"""

from __future__ import annotations
import os
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional
from datetime import datetime


class PermissionLevel(Enum):
    """Permission tiers from least to most restrictive."""
    AUTONOMOUS = "autonomous"      # No approval needed
    NOTIFY = "notify"              # Log but proceed
    CONFIRM = "confirm"            # Require explicit user confirmation
    DENY = "deny"                  # Blocked unless policy override


class ToolCategory(Enum):
    """Categories of tools/operations."""
    FILES = "files"
    CODE = "code"
    WEB = "web"
    TERMINAL = "terminal"
    GIT = "git"
    APIS = "apis"
    DATABASE = "database"


class OperationType(Enum):
    """Types of operations within categories."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    EXTERNAL_ACTION = "external_action"


@dataclass
class PermissionRule:
    """A single permission rule."""
    category: ToolCategory
    operation: OperationType
    level: PermissionLevel
    # Optional: path patterns, command patterns, etc.
    patterns: list[str] = field(default_factory=list)
    # Optional: conditions (e.g., "file_size < 10MB")
    conditions: list[str] = field(default_factory=list)
    # Human-readable reason for this rule
    reason: str = ""


@dataclass
class ApprovalRequest:
    """A request for user approval."""
    id: str
    timestamp: str
    category: ToolCategory
    operation: OperationType
    description: str
    details: dict
    status: str = "pending"  # pending, approved, denied, expired
    expires_at: Optional[str] = None
    response: Optional[str] = None


class PermissionsEngine:
    """
    Evaluates operations against permission rules.
    
    Default policy (JARVIS-like autonomy):
    - READ operations: AUTONOMOUS
    - WRITE (temp files, tests, project modifications): AUTONOMOUS
    - WRITE (important configs, secrets): CONFIRM
    - EXECUTE (tests, build, lint): AUTONOMOUS
    - EXECUTE (deploy, production scripts): CONFIRM
    - DELETE (temp, cache): AUTONOMOUS
    - DELETE (important data, git history): CONFIRM
    - EXTERNAL_ACTION (API calls, web requests): CONFIRM
    """

    def __init__(self, root: Path, policy_file: Optional[Path] = None):
        self.root = root
        self.policy_file = policy_file or root / ".agent" / "orion" / "permissions.json"
        self.rules: list[PermissionRule] = []
        self.pending_approvals: dict[str, ApprovalRequest] = {}
        self.approval_history: list[ApprovalRequest] = []
        self._load_policy()

    def _load_policy(self):
        """Load permission rules from policy file or use defaults."""
        if self.policy_file.exists():
            try:
                data = json.loads(self.policy_file.read_text(encoding="utf-8"))
                self.rules = [PermissionRule(**r) for r in data.get("rules", [])]
            except Exception:
                self._default_policy()
        else:
            self._default_policy()
            self._save_policy()

    def _default_policy(self):
        """Default JARVIS-like autonomy policy."""
        self.rules = [
            # FILES
            PermissionRule(ToolCategory.FILES, OperationType.READ, PermissionLevel.AUTONOMOUS,
                reason="Reading files is safe and necessary for context"),
            PermissionRule(ToolCategory.FILES, OperationType.WRITE, PermissionLevel.AUTONOMOUS,
                patterns=["**/tmp/**", "**/temp/**", "**/*.tmp", "**/*.temp", "**/experiments/**"],
                reason="Temporary/experimental files are safe to create"),
            PermissionRule(ToolCategory.FILES, OperationType.WRITE, PermissionLevel.AUTONOMOUS,
                patterns=["**/tests/**", "**/test_*.py", "**/*_test.py", "**/__pycache__/**"],
                reason="Test files are safe to create/modify"),
            PermissionRule(ToolCategory.FILES, OperationType.WRITE, PermissionLevel.AUTONOMOUS,
                patterns=["**/*.md", "**/*.txt", "**/*.json", "**/*.yaml", "**/*.yml"],
                reason="Documentation and config files are normally safe"),
            PermissionRule(ToolCategory.FILES, OperationType.WRITE, PermissionLevel.CONFIRM,
                patterns=["**/.env*", "**/secrets/**", "**/credentials/**", "**/*.key", "**/*.pem"],
                reason="Secrets and credentials require confirmation"),
            PermissionRule(ToolCategory.FILES, OperationType.WRITE, PermissionLevel.CONFIRM,
                patterns=["**/package.json", "**/requirements.txt", "**/pyproject.toml", "**/Cargo.toml"],
                reason="Dependency manifests affect entire project"),
            PermissionRule(ToolCategory.FILES, OperationType.DELETE, PermissionLevel.AUTONOMOUS,
                patterns=["**/tmp/**", "**/temp/**", "**/*.tmp", "**/*.temp", "**/__pycache__/**", "**/*.pyc"],
                reason="Cleanup of temp/cache files is safe"),
            PermissionRule(ToolCategory.FILES, OperationType.DELETE, PermissionLevel.CONFIRM,
                patterns=["**/.git/**", "**/*.db", "**/*.sqlite", "**/data/**", "**/production/**"],
                reason="Deleting data, git history, or production files requires confirmation"),

            # CODE
            PermissionRule(ToolCategory.CODE, OperationType.READ, PermissionLevel.AUTONOMOUS,
                reason="Reading code is safe"),
            PermissionRule(ToolCategory.CODE, OperationType.WRITE, PermissionLevel.AUTONOMOUS,
                patterns=["**/experiments/**", "**/tests/**", "**/test_*.py"],
                reason="Experimental and test code changes are safe"),
            PermissionRule(ToolCategory.CODE, OperationType.WRITE, PermissionLevel.AUTONOMOUS,
                reason="Normal project code modifications are autonomous"),
            PermissionRule(ToolCategory.CODE, OperationType.EXECUTE, PermissionLevel.AUTONOMOUS,
                patterns=["**/test_*.py", "**/*_test.py", "**/tests/**", "pytest", "jest", "npm test"],
                reason="Running tests is safe and encouraged"),
            PermissionRule(ToolCategory.CODE, OperationType.EXECUTE, PermissionLevel.AUTONOMOUS,
                patterns=["lint", "format", "typecheck", "mypy", "ruff", "eslint", "prettier"],
                reason="Linting/formatting/type-checking are safe"),
            PermissionRule(ToolCategory.CODE, OperationType.EXECUTE, PermissionLevel.CONFIRM,
                patterns=["deploy", "release", "publish", "docker push", "kubectl apply", "terraform apply"],
                reason="Production deployment requires confirmation"),
            PermissionRule(ToolCategory.CODE, OperationType.DELETE, PermissionLevel.CONFIRM,
                patterns=["**/src/**", "**/lib/**", "**/app/**", "**/core/**"],
                reason="Deleting core source code requires confirmation"),

            # WEB
            PermissionRule(ToolCategory.WEB, OperationType.READ, PermissionLevel.AUTONOMOUS,
                reason="Web search and reading documentation is safe"),
            PermissionRule(ToolCategory.WEB, OperationType.WRITE, PermissionLevel.CONFIRM,
                reason="Posting data to web endpoints requires confirmation"),
            PermissionRule(ToolCategory.WEB, OperationType.EXECUTE, PermissionLevel.CONFIRM,
                reason="Web actions with side effects require confirmation"),
            PermissionRule(ToolCategory.WEB, OperationType.EXTERNAL_ACTION, PermissionLevel.CONFIRM,
                reason="External API calls with side effects require confirmation"),

            # TERMINAL
            PermissionRule(ToolCategory.TERMINAL, OperationType.READ, PermissionLevel.AUTONOMOUS,
                patterns=["ls", "dir", "cat", "type", "head", "tail", "grep", "find", "tree", "pwd", "git status", "git log", "git diff"],
                reason="Read-only terminal commands are safe"),
            PermissionRule(ToolCategory.TERMINAL, OperationType.EXECUTE, PermissionLevel.AUTONOMOUS,
                patterns=["pytest", "python -m pytest", "npm test", "npm run test", "cargo test", "go test", "make test", "lint", "format", "build", "compile"],
                reason="Standard dev commands (test, lint, build) are autonomous"),
            PermissionRule(ToolCategory.TERMINAL, OperationType.EXECUTE, PermissionLevel.AUTONOMOUS,
                patterns=["pip install", "npm install", "yarn install", "cargo build", "go mod tidy"],
                reason="Dependency installation in dev environment is autonomous"),
            PermissionRule(ToolCategory.TERMINAL, OperationType.EXECUTE, PermissionLevel.CONFIRM,
                patterns=["sudo", "rm -rf", "dd ", "mkfs", "fdisk", "systemctl", "service ", "docker run --privileged", "kubectl delete", "terraform destroy"],
                reason="Privileged/destructive system commands require confirmation"),
            PermissionRule(ToolCategory.TERMINAL, OperationType.EXECUTE, PermissionLevel.CONFIRM,
                patterns=["curl -X POST", "curl -X PUT", "curl -X DELETE", "wget --post", "http POST", "http PUT", "http DELETE"],
                reason="Mutating HTTP requests require confirmation"),

            # GIT
            PermissionRule(ToolCategory.GIT, OperationType.READ, PermissionLevel.AUTONOMOUS,
                reason="Git read operations (status, log, diff, show) are safe"),
            PermissionRule(ToolCategory.GIT, OperationType.WRITE, PermissionLevel.AUTONOMOUS,
                patterns=["git add", "git commit", "git checkout -b", "git branch", "git stash"],
                reason="Local git operations are autonomous"),
            PermissionRule(ToolCategory.GIT, OperationType.WRITE, PermissionLevel.CONFIRM,
                patterns=["git push", "git push --force", "git tag", "git rebase", "git reset --hard"],
                reason="Remote pushes, force operations, history rewriting require confirmation"),
            PermissionRule(ToolCategory.GIT, OperationType.DELETE, PermissionLevel.CONFIRM,
                patterns=["git branch -D", "git tag -d", "git push --delete"],
                reason="Deleting branches/tags remotely requires confirmation"),

            # APIs
            PermissionRule(ToolCategory.APIS, OperationType.READ, PermissionLevel.AUTONOMOUS,
                patterns=["GET "],
                reason="API GET requests are safe"),
            PermissionRule(ToolCategory.APIS, OperationType.WRITE, PermissionLevel.CONFIRM,
                patterns=["POST ", "PUT ", "PATCH "],
                reason="Mutating API requests require confirmation"),
            PermissionRule(ToolCategory.APIS, OperationType.DELETE, PermissionLevel.CONFIRM,
                patterns=["DELETE "],
                reason="API DELETE requests require confirmation"),
            PermissionRule(ToolCategory.APIS, OperationType.EXTERNAL_ACTION, PermissionLevel.CONFIRM,
                reason="External API actions with side effects require confirmation"),

            # DATABASE
            PermissionRule(ToolCategory.DATABASE, OperationType.READ, PermissionLevel.AUTONOMOUS,
                patterns=["SELECT ", "SHOW ", "DESCRIBE ", "EXPLAIN "],
                reason="Read-only database queries are safe"),
            PermissionRule(ToolCategory.DATABASE, OperationType.WRITE, PermissionLevel.CONFIRM,
                patterns=["INSERT ", "UPDATE ", "CREATE ", "ALTER "],
                reason="Database modifications require confirmation"),
            PermissionRule(ToolCategory.DATABASE, OperationType.DELETE, PermissionLevel.CONFIRM,
                patterns=["DELETE ", "DROP ", "TRUNCATE "],
                reason="Database deletions require confirmation"),
            PermissionRule(ToolCategory.DATABASE, OperationType.EXECUTE, PermissionLevel.CONFIRM,
                patterns=["MIGRATE", "BACKUP", "RESTORE"],
                reason="Database admin operations require confirmation"),
        ]

    def _save_policy(self):
        """Save current policy to file."""
        self.policy_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0",
            "updated": datetime.now().isoformat(),
            "rules": [
                {
                    "category": r.category.value,
                    "operation": r.operation.value,
                    "level": r.level.value,
                    "patterns": r.patterns,
                    "conditions": r.conditions,
                    "reason": r.reason
                }
                for r in self.rules
            ]
        }
        self.policy_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def evaluate(self, category: ToolCategory, operation: OperationType, 
                 description: str, details: dict = None) -> PermissionLevel:
        """
        Evaluate an operation against permission rules.
        Returns the highest restriction level that matches.
        """
        details = details or {}
        matched_levels = []

        for rule in self.rules:
            if rule.category != category or rule.operation != operation:
                continue

            # Check patterns if specified
            if rule.patterns:
                matched = False
                for pattern in rule.patterns:
                    if self._match_pattern(pattern, description, details):
                        matched = True
                        break
                if not matched:
                    continue

            matched_levels.append(rule.level)

        if not matched_levels:
            # Default: CONFIRM for unknown operations (safe default)
            return PermissionLevel.CONFIRM

        # Return most restrictive level
        priority = {
            PermissionLevel.DENY: 4,
            PermissionLevel.CONFIRM: 3,
            PermissionLevel.NOTIFY: 2,
            PermissionLevel.AUTONOMOUS: 1
        }
        return max(matched_levels, key=lambda l: priority[l])

    def _match_pattern(self, pattern: str, description: str, details: dict) -> bool:
        """Match a pattern against description and details."""
        # Simple glob-style matching
        import fnmatch
        text = (description + " " + " ".join(str(v) for v in details.values())).lower()
        pattern_lower = pattern.lower()
        
        # Convert glob to regex-like
        if "*" in pattern_lower or "?" in pattern_lower:
            return fnmatch.fnmatch(text, pattern_lower)
        return pattern_lower in text

    def request_approval(self, category: ToolCategory, operation: OperationType,
                         description: str, details: dict = None, 
                         ttl_seconds: int = 300) -> ApprovalRequest:
        """Create an approval request for user confirmation."""
        import uuid
        request_id = f"appr-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        from datetime import timedelta
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        
        request = ApprovalRequest(
            id=request_id,
            timestamp=datetime.now().isoformat(),
            category=category,
            operation=operation,
            description=description,
            details=details or {},
            expires_at=expires_at.isoformat()
        )
        
        self.pending_approvals[request_id] = request
        return request

    def respond_approval(self, request_id: str, approved: bool, response: str = "") -> bool:
        """Record user response to approval request."""
        if request_id not in self.pending_approvals:
            return False
        
        request = self.pending_approvals[request_id]
        request.status = "approved" if approved else "denied"
        request.response = response
        self.approval_history.append(request)
        del self.pending_approvals[request_id]
        return True

    def get_pending_approvals(self) -> list[ApprovalRequest]:
        """Get all pending approval requests."""
        # Clean expired
        now = datetime.now()
        expired = [rid for rid, req in self.pending_approvals.items() 
                   if datetime.fromisoformat(req.expires_at) < now]
        for rid in expired:
            req = self.pending_approvals[rid]
            req.status = "expired"
            self.approval_history.append(req)
            del self.pending_approvals[rid]
        
        return list(self.pending_approvals.values())

    def add_rule(self, rule: PermissionRule):
        """Add a custom permission rule."""
        self.rules.append(rule)
        self._save_policy()

    def remove_rule(self, category: ToolCategory, operation: OperationType, index: int = -1) -> bool:
        """Remove a permission rule."""
        matching = [i for i, r in enumerate(self.rules) 
                    if r.category == category and r.operation == operation]
        if not matching:
            return False
        idx = matching[index] if index >= 0 else matching[-1]
        self.rules.pop(idx)
        self._save_policy()
        return True


class ToolRegistry:
    """
    Registry of available tools with their permission requirements.
    Each tool declares its category, operation type, and risk level.
    """

    def __init__(self, permissions: PermissionsEngine):
        self.permissions = permissions
        self.tools: dict[str, dict] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Register default tools with their permission profiles."""
        
        # FILE TOOLS
        self.register("read_file", ToolCategory.FILES, OperationType.READ,
            "Read a file from the filesystem",
            {"path": "string", "start_line": "int?", "end_line": "int?"})
        
        self.register("write_file", ToolCategory.FILES, OperationType.WRITE,
            "Write content to a file",
            {"path": "string", "content": "string"})
        
        self.register("edit_file", ToolCategory.FILES, OperationType.WRITE,
            "Edit a file (find/replace)",
            {"path": "string", "find": "string", "replace": "string"})
        
        self.register("delete_file", ToolCategory.FILES, OperationType.DELETE,
            "Delete a file",
            {"path": "string"})
        
        self.register("list_files", ToolCategory.FILES, OperationType.READ,
            "List directory contents",
            {"path": "string?"})
        
        self.register("glob_search", ToolCategory.FILES, OperationType.READ,
            "Find files by glob pattern",
            {"pattern": "string", "path": "string?"})

        # CODE TOOLS
        self.register("run_tests", ToolCategory.CODE, OperationType.EXECUTE,
            "Run test suite",
            {"command": "string?", "path": "string?"})
        
        self.register("lint_code", ToolCategory.CODE, OperationType.EXECUTE,
            "Run linter/formatter",
            {"command": "string?", "path": "string?"})
        
        self.register("build_project", ToolCategory.CODE, OperationType.EXECUTE,
            "Build the project",
            {"command": "string?", "path": "string?"})
        
        self.register("deploy", ToolCategory.CODE, OperationType.EXECUTE,
            "Deploy to production",
            {"target": "string", "command": "string"})

        # TERMINAL TOOLS
        self.register("run_command", ToolCategory.TERMINAL, OperationType.EXECUTE,
            "Execute a shell command",
            {"command": "string", "cwd": "string?", "wait": "string?"})
        
        self.register("run_background", ToolCategory.TERMINAL, OperationType.EXECUTE,
            "Start a background process",
            {"command": "string", "cwd": "string?"})

        # GIT TOOLS
        self.register("git_status", ToolCategory.GIT, OperationType.READ,
            "Get git status",
            {})
        
        self.register("git_commit", ToolCategory.GIT, OperationType.WRITE,
            "Create a git commit",
            {"message": "string", "files": "string[]?"})
        
        self.register("git_push", ToolCategory.GIT, OperationType.WRITE,
            "Push to remote",
            {"remote": "string?", "branch": "string?", "force": "bool?"})
        
        self.register("git_branch", ToolCategory.GIT, OperationType.WRITE,
            "Create/delete branch",
            {"name": "string", "delete": "bool?"})

        # WEB TOOLS
        self.register("web_search", ToolCategory.WEB, OperationType.READ,
            "Search the web",
            {"query": "string", "count": "int?"})
        
        self.register("web_fetch", ToolCategory.WEB, OperationType.READ,
            "Fetch a web page",
            {"url": "string"})

        # API TOOLS
        self.register("api_get", ToolCategory.APIS, OperationType.READ,
            "GET request to API",
            {"url": "string", "headers": "object?"})
        
        self.register("api_post", ToolCategory.APIS, OperationType.WRITE,
            "POST request to API",
            {"url": "string", "data": "object", "headers": "object?"})
        
        self.register("api_delete", ToolCategory.APIS, OperationType.DELETE,
            "DELETE request to API",
            {"url": "string", "headers": "object?"})

        # DATABASE TOOLS
        self.register("db_query", ToolCategory.DATABASE, OperationType.READ,
            "Execute SELECT query",
            {"query": "string", "params": "array?"})
        
        self.register("db_execute", ToolCategory.DATABASE, OperationType.WRITE,
            "Execute INSERT/UPDATE/CREATE",
            {"query": "string", "params": "array?"})

    def register(self, name: str, category: ToolCategory, operation: OperationType,
                 description: str, params: dict):
        """Register a tool."""
        self.tools[name] = {
            "name": name,
            "category": category,
            "operation": operation,
            "description": description,
            "params": params
        }

    def get_tool(self, name: str) -> Optional[dict]:
        """Get tool definition."""
        return self.tools.get(name)

    def list_tools(self, category: ToolCategory = None) -> list[dict]:
        """List tools, optionally filtered by category."""
        if category:
            return [t for t in self.tools.values() if t["category"] == category]
        return list(self.tools.values())

    def check_permission(self, tool_name: str, args: dict = None) -> PermissionLevel:
        """Check permission level for a tool with given arguments."""
        tool = self.tools.get(tool_name)
        if not tool:
            return PermissionLevel.DENY
        
        # Build description from tool name and args
        desc = f"{tool_name} {args}" if args else tool_name
        return self.permissions.evaluate(
            tool["category"], 
            tool["operation"], 
            desc, 
            args or {}
        )

    def request_tool_approval(self, tool_name: str, args: dict = None) -> Optional[ApprovalRequest]:
        """Request approval for a tool if needed."""
        tool = self.tools.get(tool_name)
        if not tool:
            return None
        
        level = self.check_permission(tool_name, args)
        if level in (PermissionLevel.AUTONOMOUS, PermissionLevel.NOTIFY):
            return None  # No approval needed
        
        return self.permissions.request_approval(
            tool["category"],
            tool["operation"],
            f"Execute {tool_name}",
            args or {}
        )
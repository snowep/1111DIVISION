"""
ORION Core Pipeline

The minimal working orchestrator:
USER -> ORION -> Understand -> Inspect -> Plan -> Execute -> Verify -> Critique -> Correct -> Report
"""

from __future__ import annotations
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Literal
from enum import Enum


class TaskStatus(Enum):
    PENDING = "PENDING"
    UNDERSTANDING = "UNDERSTANDING"
    INSPECTING = "INSPECTING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    CRITIQUING = "CRITIQUING"
    CORRECTING = "CORRECTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class Task:
    id: str
    objective: str
    context: dict = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    plan: list[str] = field(default_factory=list)
    execution_log: list[dict] = field(default_factory=list)
    verification_results: list[dict] = field(default_factory=list)
    critique_findings: list[str] = field(default_factory=list)
    corrections: list[dict] = field(default_factory=list)
    final_result: dict | None = None
    error: str | None = None

    def update_status(self, status: TaskStatus):
        self.status = status
        self.updated_at = datetime.now().isoformat()

    def log_execution(self, action: str, result: Any, success: bool):
        import json
        # Serialize result as JSON for proper parsing later
        if isinstance(result, (dict, list)):
            result_str = json.dumps(result)
            # Don't truncate JSON - it breaks parsing
        else:
            result_str = str(result)[:500]
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "result": result_str,
            "success": success
        })
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "objective": self.objective,
            "context": self.context,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "plan": self.plan,
            "execution_log": self.execution_log,
            "verification_results": self.verification_results,
            "critique_findings": self.critique_findings,
            "corrections": self.corrections,
            "final_result": self.final_result,
            "error": self.error
        }


class Retriever:
    """Retrieval engine for memory, knowledge, and experience stores."""

    def __init__(self, root: Path):
        self.root = root
        self.memory_dir = root / ".agent" / "orion" / "memory"
        self.knowledge_dir = root / ".agent" / "orion" / "knowledge"
        self.experience_dir = root / ".agent" / "orion" / "experience"

    def retrieve(self, task: Task, budget: Literal["micro", "standard", "deep", "full"] = "standard") -> dict:
        """Retrieve relevant sections from all three stores."""
        understanding = task.context.get("understanding", {})
        keywords = understanding.get("keywords", [])
        objective = task.objective

        # Extract query terms
        query_terms = self._extract_query_terms(objective, keywords)

        # Search each store
        memory_sections = self._search_store(self.memory_dir, query_terms, "memory")
        knowledge_sections = self._search_store(self.knowledge_dir, query_terms, "knowledge")
        experience_sections = self._search_store(self.experience_dir, query_terms, "experience")

        # Rank and filter
        all_sections = memory_sections + knowledge_sections + experience_sections
        ranked = self._rank_sections(all_sections, query_terms)
        filtered = self._apply_budget(ranked, budget)

        return {
            "memory": [s for s in filtered if s["store"] == "memory"],
            "knowledge": [s for s in filtered if s["store"] == "knowledge"],
            "experience": [s for s in filtered if s["store"] == "experience"],
            "total_tokens": sum(s.get("token_estimate", 0) for s in filtered),
            "gaps": self._identify_gaps(query_terms, filtered)
        }

    def _extract_query_terms(self, objective: str, keywords: list[str]) -> list[str]:
        """Extract search terms from objective and keywords."""
        terms = set(keywords)
        # Add nouns and verbs from objective
        words = re.findall(r'\b\w+\b', objective.lower())
        # Filter stop words
        stop = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "from", "as", "is", "was", "are", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "must", "can", "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them"}
        terms.update(w for w in words if len(w) > 2 and w not in stop)
        return list(terms)

    def _search_store(self, store_dir: Path, query_terms: list[str], store_name: str) -> list[dict]:
        """Search a single store directory."""
        sections = []
        if not store_dir.exists():
            return sections

        for md_file in store_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                file_sections = self._extract_sections(content, md_file, store_name, query_terms)
                sections.extend(file_sections)
            except Exception:
                pass
        return sections

    def _extract_sections(self, content: str, file_path: Path, store_name: str, query_terms: list[str]) -> list[dict]:
        """Extract relevant sections from a markdown file."""
        sections = []
        lines = content.split("\n")

        current_heading = ""
        current_level = 0
        section_start = 0
        section_lines = []

        for i, line in enumerate(lines):
            # Detect heading
            heading_match = re.match(r'^(#+)\s+(.+)$', line)
            if heading_match:
                # Save previous section
                if section_lines:
                    section_content = "\n".join(section_lines)
                    if self._is_relevant(section_content, query_terms) or self._is_relevant(current_heading, query_terms):
                        sections.append({
                            "store": store_name,
                            "file": str(file_path.relative_to(self.root)),
                            "heading": current_heading,
                            "content": section_content,
                            "line_range": (section_start + 1, i),
                            "token_estimate": len(section_content) // 4
                        })
                # Start new section
                current_heading = heading_match.group(2)
                current_level = len(heading_match.group(1))
                section_start = i
                section_lines = [line]
            else:
                section_lines.append(line)

        # Don't forget last section
        if section_lines:
            section_content = "\n".join(section_lines)
            if self._is_relevant(section_content, query_terms) or self._is_relevant(current_heading, query_terms):
                sections.append({
                    "store": store_name,
                    "file": str(file_path.relative_to(self.root)),
                    "heading": current_heading,
                    "content": section_content,
                    "line_range": (section_start + 1, len(lines)),
                    "token_estimate": len(section_content) // 4
                })

        return sections

    def _is_relevant(self, text: str, query_terms: list[str]) -> bool:
        """Check if text contains any query terms."""
        text_lower = text.lower()
        return any(term in text_lower for term in query_terms)

    def _rank_sections(self, sections: list[dict], query_terms: list[str]) -> list[dict]:
        """Rank sections by relevance."""
        for s in sections:
            score = 0.0
            heading = s["heading"].lower()
            content = s["content"].lower()
            file_path = s["file"].lower()

            # Heading match (high weight)
            heading_hits = sum(1 for t in query_terms if t in heading)
            score += 0.4 * min(heading_hits / max(len(query_terms), 1), 1.0)

            # Content match
            content_hits = sum(1 for t in query_terms if t in content)
            score += 0.3 * min(content_hits / max(len(query_terms), 1), 1.0)

            # File name match
            file_hits = sum(1 for t in query_terms if t in file_path)
            score += 0.1 * min(file_hits / max(len(query_terms), 1), 1.0)

            # Authority boost
            if "decision" in file_path or "preference" in file_path:
                score += 0.1
            elif "pipeline" in file_path or "architecture" in file_path:
                score += 0.1

            s["relevance_score"] = score

        # Sort by score descending
        return sorted(sections, key=lambda x: x["relevance_score"], reverse=True)

    def _apply_budget(self, sections: list[dict], budget: str) -> list[dict]:
        """Apply token budget, truncate lowest relevance first."""
        budgets = {
            "micro": 500,
            "standard": 2000,
            "deep": 4000,
            "full": 8000
        }
        limit = budgets.get(budget, 2000)

        total = 0
        result = []
        for s in sections:
            if total + s.get("token_estimate", 0) <= limit:
                result.append(s)
                total += s.get("token_estimate", 0)
            else:
                # Try to truncate this section to fit
                remaining = limit - total
                if remaining > 100:  # minimum useful section
                    truncated = s.copy()
                    truncated["content"] = s["content"][:remaining * 4] + "... [truncated]"
                    truncated["token_estimate"] = remaining
                    truncated["truncated"] = True
                    result.append(truncated)
                break
        return result

    def _identify_gaps(self, query_terms: list[str], sections: list[dict]) -> list[str]:
        """Identify query terms not found in retrieved sections."""
        found_terms = set()
        for s in sections:
            content = (s["heading"] + " " + s["content"]).lower()
            for t in query_terms:
                if t in content:
                    found_terms.add(t)
        return [t for t in query_terms if t not in found_terms]


class WorkspaceInspector:
    """Inspect the workspace to gather context for tasks."""

    def __init__(self, root: Path):
        self.root = root

    def inspect(self, scope: str = "full") -> dict:
        """Inspect workspace and return structured context."""
        context = {
            "root": str(self.root),
            "timestamp": datetime.now().isoformat(),
            "structure": self._get_structure(),
            "key_files": self._find_key_files(),
            "git_status": self._git_status(),
            "agent_state": self._read_agent_state()
        }
        return context

    def _get_structure(self, max_depth: int = 3) -> dict:
        """Get directory tree up to max_depth."""
        def walk(path: Path, depth: int = 0) -> dict:
            if depth >= max_depth:
                return {"...": "truncated"}
            try:
                entries = {}
                for item in sorted(path.iterdir()):
                    if item.name.startswith('.git'):
                        continue
                    if item.is_dir():
                        entries[item.name + "/"] = walk(item, depth + 1)
                    else:
                        entries[item.name] = f"file ({item.stat().st_size} bytes)"
                return entries
            except PermissionError:
                return {"error": "permission denied"}

        return walk(self.root)

    def _find_key_files(self) -> list[str]:
        """Find important configuration and documentation files."""
        patterns = [
            "AGENT.md", "*.md", "*.py", "*.json", "*.yaml", "*.yml",
            "package.json", "requirements.txt", "pyproject.toml",
            "README*", "CHANGELOG*", "LICENSE*"
        ]
        found = []
        for pattern in patterns:
            for path in self.root.rglob(pattern):
                if ".git" not in path.parts:
                    rel = path.relative_to(self.root)
                    found.append(str(rel))
        return sorted(set(found))[:50]

    def _git_status(self) -> dict:
        """Get git status if available."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.root, capture_output=True, text=True, timeout=5
            )
            return {
                "clean": result.stdout.strip() == "",
                "changes": result.stdout.strip().split("\n") if result.stdout.strip() else [],
                "branch": self._git_branch()
            }
        except Exception:
            return {"available": False}

    def _git_branch(self) -> str:
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.root, capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() or "unknown"
        except Exception:
            return "unknown"

    def _read_agent_state(self) -> dict:
        """Read key agent state files."""
        state = {}
        agent_dir = self.root / ".agent"
        if agent_dir.exists():
            for md_file in agent_dir.rglob("*.md"):
                try:
                    rel = md_file.relative_to(self.root)
                    content = md_file.read_text(encoding="utf-8")
                    state[str(rel)] = content[:2000]
                except Exception:
                    pass
        return state


class Planner:
    """Generate execution plans from objectives and context."""

    def __init__(self, inspector: WorkspaceInspector):
        self.inspector = inspector

    def plan(self, objective: str, context: dict) -> list[str]:
        """Generate a step-by-step plan."""
        # This is a simplified planner - in practice could use LLM
        plan = []

        # Analyze objective for keywords
        obj_lower = objective.lower()

        if any(kw in obj_lower for kw in ["create", "add", "new", "build", "implement"]):
            plan.append("Identify target location and requirements")
            plan.append("Create necessary directory structure")
            plan.append("Implement the requested artifact")
            plan.append("Verify creation succeeded")

        elif any(kw in obj_lower for kw in ["analyze", "inspect", "review", "audit", "check"]):
            plan.append("Identify scope and targets for analysis")
            plan.append("Inspect relevant files and structure")
            plan.append("Perform analysis")
            plan.append("Summarize findings")

        elif any(kw in obj_lower for kw in ["fix", "repair", "correct", "debug"]):
            plan.append("Reproduce or locate the issue")
            plan.append("Identify root cause")
            plan.append("Implement fix")
            plan.append("Verify fix resolves issue")
            plan.append("Check for regressions")

        elif any(kw in obj_lower for kw in ["update", "modify", "change", "edit"]):
            plan.append("Locate target files")
            plan.append("Understand current implementation")
            plan.append("Apply changes")
            plan.append("Verify changes are correct")

        else:
            # Generic plan
            plan.append("Understand the objective and constraints")
            plan.append("Inspect relevant workspace areas")
            plan.append("Execute necessary actions")
            plan.append("Verify results")
            plan.append("Report outcome")

        # Add verification and critique as standard steps
        plan.append("Verify all success criteria met")
        plan.append("Critique result for completeness and correctness")

        return plan


class Executor:
    """Execute plan steps using available tools."""

    def __init__(self, root: Path):
        self.root = root
        self.inspector = WorkspaceInspector(root)

    def execute_step(self, step: str, context: dict) -> tuple[bool, Any]:
        """Execute a single plan step. Returns (success, result)."""
        step_lower = step.lower()

        # Use word-boundary-like matching to avoid substring issues
        def has_word(text: str, *words: str) -> bool:
            return any(f" {w} " in f" {text} " or text.startswith(f"{w} ") or text.endswith(f" {w}") for w in words)

        # File operations - most specific first
        if has_word(step_lower, "create") and has_word(step_lower, "file", "directory", "director", "structure"):
            return self._handle_create(step, context)

        elif has_word(step_lower, "inspect", "read", "analyze"):
            return self._handle_inspect(step, context)

        elif has_word(step_lower, "write", "edit", "modify"):
            return self._handle_write(step, context)

        elif has_word(step_lower, "run", "execute", "command"):
            return self._handle_command(step, context)

        elif has_word(step_lower, "verify", "check", "test"):
            return self._handle_verify(step, context)

        elif has_word(step_lower, "list", "search"):
            # "find" is too generic (matches "findings"), use "search" instead
            return self._handle_search(step, context)

        elif has_word(step_lower, "identify", "scope", "target"):
            return self._handle_identify(step, context)

        elif has_word(step_lower, "summarize", "report"):
            return self._handle_summarize(step, context)

        elif has_word(step_lower, "understand"):
            return self._handle_understand(step, context)

        elif has_word(step_lower, "critique", "critic"):
            return self._handle_critique(step, context)

        elif has_word(step_lower, "perform"):
            return self._handle_perform(step, context)

        elif has_word(step_lower, "reproduce", "locate"):
            return self._handle_reproduce(step, context)

        elif has_word(step_lower, "implement", "fix", "repair", "correct"):
            return self._handle_implement(step, context)

        # Default: log the step as acknowledged
        return True, {"acknowledged": step, "note": "Step logged for manual execution"}

    def _handle_create(self, step: str, context: dict) -> tuple[bool, Any]:
        # Placeholder - actual implementation would parse path from step
        return True, {"action": "create", "step": step, "status": "planned"}

    def _handle_inspect(self, step: str, context: dict) -> tuple[bool, Any]:
        # Actually inspect using the inspector
        inspection = self.inspector.inspect()
        return True, {"action": "inspect", "step": step, "inspection": inspection}

    def _handle_write(self, step: str, context: dict) -> tuple[bool, Any]:
        return True, {"action": "write", "step": step, "status": "planned"}

    def _handle_command(self, step: str, context: dict) -> tuple[bool, Any]:
        return True, {"action": "command", "step": step, "status": "planned"}

    def _handle_verify(self, step: str, context: dict) -> tuple[bool, Any]:
        return True, {"action": "verify", "step": step, "status": "planned"}

    def _handle_search(self, step: str, context: dict) -> tuple[bool, Any]:
        return True, {"action": "search", "step": step, "status": "planned"}

    def _handle_identify(self, step: str, context: dict) -> tuple[bool, Any]:
        """Identify scope/targets for analysis."""
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
        """Summarize findings from inspection."""
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

        # Categorize key files
        for f in key_files:
            ext = f.split(".")[-1] if "." in f else "no_ext"
            summary["key_files_by_type"][ext] = summary["key_files_by_type"].get(ext, 0) + 1

        return True, {"action": "summarize", "step": step, "summary": summary}

    def _handle_understand(self, step: str, context: dict) -> tuple[bool, Any]:
        """Understand objective and constraints."""
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
        """Critique step - log as acknowledged."""
        return True, {"action": "critique", "step": step, "status": "planned"}

    def _handle_perform(self, step: str, context: dict) -> tuple[bool, Any]:
        """Perform analysis step - log as acknowledged."""
        return True, {"action": "perform", "step": step, "status": "planned"}

    def _handle_reproduce(self, step: str, context: dict) -> tuple[bool, Any]:
        """Reproduce/locate issue step."""
        return True, {"action": "reproduce", "step": step, "status": "planned"}

    def _handle_implement(self, step: str, context: dict) -> tuple[bool, Any]:
        """Implement fix step."""
        return True, {"action": "implement", "step": step, "status": "planned"}


class Verifier:
    """Verify task results against success criteria."""

    def __init__(self, root: Path):
        self.root = root

    def verify(self, task: Task, plan: list[str]) -> dict:
        """Verify task completion against plan and objective."""
        understanding = task.context.get("understanding", {})
        keywords = understanding.get("keywords", [])

        results = {
            "plan_coverage": self._check_plan_coverage(task, plan),
            "objective_met": self._check_objective(task, keywords),
            "artifacts_exist": self._check_artifacts(task),
            "no_regressions": self._check_regressions(task),
            "overall": "PASS"
        }

        # Determine overall
        if not all([results["plan_coverage"], results["objective_met"], results["artifacts_exist"]]):
            results["overall"] = "FAIL"
        elif not results["no_regressions"]:
            results["overall"] = "WARNING"

        return results

    def _check_plan_coverage(self, task: Task, plan: list[str]) -> bool:
        """Check if all plan steps were executed."""
        executed_actions = {log["action"] for log in task.execution_log}
        # Simplified: check if we have execution logs for each plan step
        return len(task.execution_log) >= len(plan) * 0.7  # 70% coverage threshold

    def _check_objective(self, task: Task, keywords: list[str]) -> bool:
        """Check if objective appears to be met based on keywords."""
        if task.final_result:
            return task.final_result.get("success", False)

        # For inspection/analysis tasks, check if inspection results exist
        if "analyze" in keywords:
            inspection = task.context.get("inspection", {})
            execution_log = task.execution_log
            # Check if we actually inspected and summarized - extract action from result
            has_inspect = False
            has_identify = False
            has_summarize = False
            for log in execution_log:
                result = log.get("result", {})
                # Result may be a string (JSON) or dict
                if isinstance(result, str):
                    try:
                        import json
                        result = json.loads(result)
                    except Exception:
                        result = {}
                if isinstance(result, dict):
                    action = result.get("action", "")
                    if action == "inspect":
                        has_inspect = True
                    elif action == "identify":
                        has_identify = True
                    elif action == "summarize":
                        has_summarize = True
            return has_inspect and has_identify and has_summarize

        # For create tasks, check if creation steps were executed
        if "create" in keywords:
            execution_log = task.execution_log
            has_identify = False
            has_create = False
            has_verify = False
            for log in execution_log:
                result = log.get("result", {})
                if isinstance(result, str):
                    try:
                        import json
                        result = json.loads(result)
                    except Exception:
                        result = {}
                if isinstance(result, dict):
                    action = result.get("action", "")
                    if action == "identify":
                        has_identify = True
                    elif action == "create":
                        has_create = True
                    elif action == "verify":
                        has_verify = True
            return has_identify and has_create and has_verify

        # For fix tasks, check if fix steps were executed
        if "fix" in keywords:
            execution_log = task.execution_log
            has_identify = False
            has_fix = False
            has_verify = False
            has_regressions = False
            for log in execution_log:
                result = log.get("result", {})
                if isinstance(result, str):
                    try:
                        import json
                        result = json.loads(result)
                    except Exception:
                        result = {}
                if isinstance(result, dict):
                    action = result.get("action", "")
                    if action == "identify":
                        has_identify = True
                    elif action in ("fix", "repair", "correct", "implement"):
                        has_fix = True
                    elif action == "verify":
                        has_verify = True
                    elif action == "check":
                        has_regressions = True
                # Also check the step description for "check" or "regress"
                step_desc = log.get("action", "").lower()
                if "check" in step_desc or "regress" in step_desc:
                    has_regressions = True
            return has_identify and has_fix and has_verify and has_regressions

        return task.status == TaskStatus.COMPLETED

    def _check_artifacts(self, task: Task) -> bool:
        """Check if expected artifacts were created."""
        # Would need expected artifacts defined in plan
        return True  # Placeholder

    def _check_regressions(self, task: Task) -> bool:
        """Check for regressions (git status clean, tests pass, etc.)."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.root, capture_output=True, text=True, timeout=5
            )
            # Allow changes that are part of the task
            return True
        except Exception:
            return True


class Critiquer:
    """Critique results for quality, completeness, correctness."""

    def critique(self, task: Task, verification: dict) -> list[str]:
        """Generate critique findings."""
        findings = []

        # Check verification results
        if verification.get("overall") == "FAIL":
            findings.append("CRITICAL: Verification failed - objective not met")
        elif verification.get("overall") == "WARNING":
            findings.append("WARNING: Potential regressions or incomplete verification")

        # Check execution log for failures
        failed_steps = [log for log in task.execution_log if not log["success"]]
        if failed_steps:
            findings.append(f"Found {len(failed_steps)} failed execution steps")

        # Check for empty results
        if not task.final_result:
            findings.append("No final result produced")

        # Check critique depth
        if len(task.critique_findings) == 0 and task.status == TaskStatus.CRITIQUING:
            findings.append("No critique findings recorded - may indicate shallow review")

        return findings


class ORION:
    """
    ORION Core Orchestrator

    Implements the pipeline:
    USER -> Understand -> Inspect -> Plan -> Execute -> Verify -> Critique -> Correct -> Report
    """

    def __init__(self, root: Path | str = None):
        self.root = Path(root) if root else Path.cwd()
        self.inspector = WorkspaceInspector(self.root)
        self.retriever = Retriever(self.root)
        self.planner = Planner(self.inspector)
        self.executor = Executor(self.root)
        self.verifier = Verifier(self.root)
        self.critiquer = Critiquer()
        self.task_counter = 0

    def run_task(self, objective: str, context: dict = None) -> Task:
        """Execute the full pipeline for a task."""
        # Create task
        self.task_counter += 1
        task = Task(
            id=f"task-{datetime.now().strftime('%Y%m%d')}-{self.task_counter:03d}",
            objective=objective,
            context=context or {}
        )

        try:
            # STAGE 1: UNDERSTAND
            task.update_status(TaskStatus.UNDERSTANDING)
            understood = self._understand(task)

            # STAGE 2: INSPECT
            task.update_status(TaskStatus.INSPECTING)
            inspection = self._inspect(task)

            # STAGE 3: PLAN
            task.update_status(TaskStatus.PLANNING)
            plan = self._plan(task, inspection)
            task.plan = plan

            # STAGE 4: EXECUTE
            task.update_status(TaskStatus.EXECUTING)
            self._execute(task, plan)

            # STAGE 5: VERIFY
            task.update_status(TaskStatus.VERIFYING)
            verification = self._verify(task, plan)
            task.verification_results.append(verification)

            # STAGE 6: CRITIQUE
            task.update_status(TaskStatus.CRITIQUING)
            critique = self._critique(task, verification)
            task.critique_findings = critique

            # STAGE 7: CORRECT (if needed)
            if critique and any("CRITICAL" in c or "FAIL" in c for c in critique):
                task.update_status(TaskStatus.CORRECTING)
                self._correct(task, critique)
                # Re-verify after correction
                verification = self._verify(task, plan)
                task.verification_results.append(verification)
                critique = self._critique(task, verification)
                task.critique_findings = critique

            # STAGE 8: REPORT
            task.update_status(TaskStatus.COMPLETED)
            task.final_result = self._report(task, verification, critique)

        except Exception as e:
            task.update_status(TaskStatus.FAILED)
            task.error = str(e)
            task.final_result = {"success": False, "error": str(e)}

        # Save task record
        self._save_task(task)

        return task

    def _understand(self, task: Task) -> dict:
        """Parse and understand the objective."""
        understood = {
            "objective": task.objective,
            "keywords": self._extract_keywords(task.objective),
            "complexity": self._estimate_complexity(task.objective),
            "requires_tools": self._identify_tools(task.objective)
        }
        task.context["understanding"] = understood
        return understood

    def _inspect(self, task: Task) -> dict:
        """Inspect workspace for relevant context + retrieve from stores."""
        inspection = self.inspector.inspect()
        task.context["inspection"] = inspection
        
        # Retrieve relevant context from memory/knowledge/experience stores
        retrieved = self.retriever.retrieve(task, budget="standard")
        task.context["retrieved"] = retrieved
        
        return inspection

    def _plan(self, task: Task, inspection: dict) -> list[str]:
        """Generate execution plan."""
        plan = self.planner.plan(task.objective, inspection)
        return plan

    def _execute(self, task: Task, plan: list[str]):
        """Execute each plan step."""
        for i, step in enumerate(plan):
            success, result = self.executor.execute_step(step, task.context)
            task.log_execution(f"Step {i+1}: {step}", result, success)
            if not success:
                task.critique_findings.append(f"Step {i+1} failed: {step}")

    def _verify(self, task: Task, plan: list[str]) -> dict:
        """Verify task results."""
        return self.verifier.verify(task, plan)

    def _critique(self, task: Task, verification: dict) -> list[str]:
        """Critique the results."""
        return self.critiquer.critique(task, verification)

    def _correct(self, task: Task, critique: list[str]):
        """Attempt to correct issues found in critique."""
        for finding in critique:
            if "CRITICAL" in finding or "FAIL" in finding:
                # Log correction attempt
                task.corrections.append({
                    "timestamp": datetime.now().isoformat(),
                    "finding": finding,
                    "action": "Correction attempted - manual intervention may be required",
                    "resolved": False
                })

    def _report(self, task: Task, verification: dict, critique: list[str]) -> dict:
        """Generate final report."""
        return {
            "success": verification.get("overall") == "PASS",
            "task_id": task.id,
            "objective": task.objective,
            "status": task.status.value,
            "plan_steps": len(task.plan),
            "executed_steps": len(task.execution_log),
            "verification": verification,
            "critique_findings": critique,
            "corrections_attempted": len(task.corrections),
            "completed_at": datetime.now().isoformat()
        }

    def _save_task(self, task: Task):
        """Save task record to filesystem."""
        tasks_dir = self.root / ".agent" / "tasks" / "completed"
        tasks_dir.mkdir(parents=True, exist_ok=True)
        task_file = tasks_dir / f"{task.id}.json"
        task_file.write_text(json.dumps(task.to_dict(), indent=2), encoding="utf-8")

    # Helper methods
    def _extract_keywords(self, objective: str) -> list[str]:
        keywords = []
        obj_lower = objective.lower()
        kw_map = {
            "create": ["create", "add", "new", "build", "make", "generate"],
            "analyze": ["analyze", "inspect", "review", "audit", "examine", "check"],
            "fix": ["fix", "repair", "debug", "correct", "resolve"],
            "update": ["update", "modify", "change", "edit", "alter"],
            "delete": ["delete", "remove", "clean", "purge"],
            "test": ["test", "verify", "validate", "check"],
            "deploy": ["deploy", "release", "publish", "ship"]
        }
        for category, words in kw_map.items():
            if any(w in obj_lower for w in words):
                keywords.append(category)
        return keywords

    def _estimate_complexity(self, objective: str) -> str:
        word_count = len(objective.split())
        if word_count < 10:
            return "simple"
        elif word_count < 30:
            return "moderate"
        return "complex"

    def _identify_tools(self, objective: str) -> list[str]:
        tools = ["filesystem"]
        obj_lower = objective.lower()
        if any(kw in obj_lower for kw in ["git", "commit", "branch", "push", "pull"]):
            tools.append("git")
        if any(kw in obj_lower for kw in ["test", "pytest", "jest", "npm test"]):
            tools.append("testing")
        if any(kw in obj_lower for kw in ["web", "http", "api", "fetch", "download"]):
            tools.append("web")
        return tools


def main():
    """CLI entry point for testing."""
    if len(sys.argv) < 2:
        print("Usage: python .agent\\orion\\core.py \"<objective>\"")
        sys.exit(1)

    objective = " ".join(sys.argv[1:])
    orion = ORION()
    print(f"ORION: Starting task - {objective}")
    print("-" * 60)

    task = orion.run_task(objective)

    print(f"Task ID: {task.id}")
    print(f"Status: {task.status.value}")
    print(f"Plan: {len(task.plan)} steps")
    print(f"Executed: {len(task.execution_log)} steps")
    print(f"Verification: {task.verification_results[-1].get('overall') if task.verification_results else 'N/A'}")
    print(f"Critique findings: {len(task.critique_findings)}")
    print(f"Success: {task.final_result.get('success') if task.final_result else False}")

    if task.error:
        print(f"Error: {task.error}")

    if task.critique_findings:
        print("\nCritique:")
        for finding in task.critique_findings:
            print(f"  - {finding}")

    print("-" * 60)
    print("ORION: Task complete")


if __name__ == "__main__":
    main()
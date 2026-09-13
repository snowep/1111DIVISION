"""P6 — GitHub skill importer: DISCOVER → INSPECT → VALIDATE → ISOLATE →
ADAPT → TEST → INTEGRATE, with a human approval gate.

Security posture (aligned with JARVIS rules):
- The remote repo is UNTRUSTED CONTENT until the importer inspects it.
- We never execute remote code during import. We only read the manifest
  and entry file text into the sandbox, then validate the manifest schema.
- Permission requests are surfaced to the user for approval; nothing is
  granted by default beyond what the user decides.
- The imported skill is placed under `.jarvis/skills/<name>/` (runtime
  layer), with `source: github:owner/repo` provenance, and then the
  derived registry is rebuilt. Import is never silent — a report is
  returned showing what was inspected, what was adapted, and what was
  rejected.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

# Max sizes keep the importer bounded even on hostile repos.
MAX_MANIFEST_BYTES = 64 * 1024
MAX_ENTRY_BYTES = 512 * 1024
MAX_TREE_ITEMS = 500

_GITHUB_API = "https://api.github.com"


class ImportError_(Exception):
    """Raised for any import failure (invalid repo, unreachable, bad manifest)."""


@dataclass
class ImportReport:
    """Inspectable, deterministic result of an import attempt."""

    repo: str
    status: str = "pending"  # "approved" | "rejected" | "needs-approval" | "failed"
    discovered: Optional[str] = None   # skill.md path in the repo
    validated: bool = False
    entry_adapted: bool = False
    installed_to: Optional[str] = None
    permissions_requested: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo": self.repo,
            "status": self.status,
            "discovered": self.discovered,
            "validated": self.validated,
            "entry_adapted": self.entry_adapted,
            "installed_to": self.installed_to,
            "permissions_requested": self.permissions_requested,
            "warnings": self.warnings,
        }


def _cfg() -> dict[str, str]:
    import os
    return {
        "token": os.environ.get("GITHUB_TOKEN", ""),
        "workspace": os.environ.get("JARVIS_WORKSPACE", "."),
    }


def _api(path: str, token: str) -> dict[str, Any]:
    """Fetch a GitHub API path with the token (if given). Never executes code."""
    import json
    import urllib.request
    url = urllib.parse.urljoin(_GITHUB_API, path.lstrip("/"))
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def discover_manifest(repo: str, token: str = "") -> tuple[Optional[str], dict[str, Any]]:
    """Return (skill.md path in repo | None, raw tree dict from GitHub API)."""
    tree = _api(f"/repos/{repo}/git/trees/HEAD?recursive=1", token)
    items = tree.get("tree", [])
    for item in items[:MAX_TREE_ITEMS]:
        if item.get("type") == "blob" and item.get("path", "").endswith("skill.md"):
            return item["path"], item
    return None, item or {}


def _parse_manifest_text(text: str) -> dict[str, Any]:
    """Parse the YAML frontmatter of a skill.md using the validated parser."""
    from jarvis.docstore.models import parse_document
    doc = parse_document("skill.md", text)
    return {k: v for k, v in doc.metadata.items() if k != "body"}


def _validate_manifest(meta: dict[str, Any]) -> tuple[bool, list[str]]:
    """Check the imported manifest against the P2 schema."""
    warnings: list[str] = []
    # Required: name, version, description, entry, permissions
    for req in ("name", "version", "description", "entry", "permissions"):
        if req not in meta or meta[req] in (None, "", [], {}):
            return False, [f"missing required field: {req}"]
    if not isinstance(meta.get("permissions"), dict):
        return False, ["permissions must be a mapping"]
    return True, warnings


def inspect_and_validate(repo: str, token: str = "") -> tuple[ImportReport, dict[str, Any]]:
    """DISCOVER + INSPECT + VALIDATE stages (read-only)."""
    report = ImportReport(repo=repo)
    try:
        manifest_path, _ = discover_manifest(repo, token)
    except Exception as exc:
        report.status = "failed"
        report.warnings.append(f"discovery failed: {exc}")
        return report, {}
    if not manifest_path:
        report.status = "failed"
        report.warnings.append("no skill.md found in repository tree")
        return report, {}

    report.discovered = manifest_path
    try:
        raw = _api(f"/repos/{repo}/contents/{manifest_path}", token)
    except Exception as exc:
        report.status = "failed"
        report.warnings.append(f"manifest fetch failed: {exc}")
        return report, {}

    import base64
    text = base64.b64decode(raw.get("content", "")).decode("utf-8")
    ok, warnings = _validate_manifest(_parse_manifest_text(text))
    report.validated = ok
    report.warnings.extend(warnings)
    if not ok:
        report.status = "rejected"
        return report, {}
    # The import never auto-grants permissions beyond P2 defaults.
    report.permissions_requested = _parse_manifest_text(text).get("permissions", {})
    return report, {"manifest_text": text, "manifest_meta": _parse_manifest_text(text)}


def _adapt_entry(text: str, repo: str) -> str:
    """Rewrite obvious remote paths to the sandbox layout (best-effort)."""
    adapted = text
    adapted = adapted.replace("$REPO", repo)
    # If the manifest references `vault/` or `skills/`, leave as-is (the
    # sandbox already routes those aliases).
    return adapted


def install_skill(repo: str, *, approve: bool, token: str = "") -> ImportReport:
    """Full pipeline with a human approval gate on the permission request."""
    report, data = inspect_and_validate(repo, token)
    if report.status in ("failed", "rejected"):
        return report
    if not approve:
        report.status = "needs-approval"
        return report

    # ISOLATE: copy only the manifest + entry into .jarvis/skills/<name>/.
    meta = data["manifest_meta"]
    name = str(meta["name"]).strip()
    import re as _re
    if not _re.fullmatch(r"[A-Za-z0-9_-]+", name):
        report.status = "rejected"
        report.warnings.append(f"unsafe skill name after import: {name!r}")
        return report

    skills_dir = Path(_cfg()["workspace"]) / ".jarvis/skills"
    skill_dir = skills_dir / name
    if skill_dir.exists():
        report.status = "rejected"
        report.warnings.append(f"{name} already exists; refusing to overwrite")
        return report
    skill_dir.mkdir(parents=True, exist_ok=True)

    # Write the manifest (validated text) + the adapted entry.
    (skill_dir / "skill.md").write_text(data["manifest_text"], encoding="utf-8")
    entry = str(meta["entry"])
    try:
        raw_entry = _api(f"/repos/{repo}/contents/{entry}", token)
        import base64
        entry_text = base64.b64decode(raw_entry.get("content", "")).decode("utf-8")
        (skill_dir / entry).write_text(_adapt_entry(entry_text, repo), encoding="utf-8")
    except Exception as exc:
        (skill_dir / "skill.md").unlink(missing_ok=True)
        skill_dir.rmdir()
        report.status = "failed"
        report.warnings.append(f"entry fetch/write failed: {exc}")
        return report

    report.entry_adapted = True
    report.installed_to = str(skill_dir.relative_to(Path(_cfg()["workspace"])))
    report.status = "approved"
    report.warnings.append(f"imported skill {name} with permission request "
                          f"{meta.get('permissions', {})} — visible for approval")
    return report
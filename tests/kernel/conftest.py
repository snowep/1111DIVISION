"""Shared fixtures for the runtime kernel test suite.

Creates a temporary directory that looks like a valid workspace:

    tmp_root/
        .git/                     # satisfies detect_repository_root
        .jarvis/
            core/
                constitution.md
                identity.md
                system-prompt.md
                world-model.md
            memory/
                active/
            personas/
                definitions/
        vault/
        council/
        src/
        tests/
        docs/
"""

from __future__ import annotations

import os
import shutil
import textwrap
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_root(tmp_path: Path) -> Path:
    """Create a fake repository root with .git + canonical structure."""
    root = tmp_path / "test-workspace"
    root.mkdir()

    # .git directory (required by detect_repository_root)
    (root / ".git").mkdir()

    # .jarvis/core/ with canonical files
    core = root / ".jarvis" / "core"
    core.mkdir(parents=True)

    (core / "constitution.md").write_text(
        textwrap.dedent("""\
            # JARVIS Constitution

            ## Core Rules

            1. Never silently repair corrupted state.
            2. No mutation without authority gate.
            3. Source priority: user > constitution > system prompt.
        """),
        encoding="utf-8",
    )

    (core / "system-prompt.md").write_text(
        textwrap.dedent("""\
            # System Prompt

            You are JARVIS. Be precise.
        """),
        encoding="utf-8",
    )

    (core / "world-model.md").write_text(
        textwrap.dedent("""\
            # World Model

            ## Project State

            Status: active.
            Phase: 10.
        """),
        encoding="utf-8",
    )

    (core / "identity.md").write_text(
        textwrap.dedent("""\
            # Identity

            Name: JARVIS
            Role: Personal Intelligence Operating System
            Primary User: the operator
            Nature: Deterministic runtime kernel
            Core Purpose: Maximize the operator's ability to think, create, research, build.

            ## Personality

            - calm
            - precise
            - observant

            ## Persona Constraints

            - never fabricate capabilities
            - never auto-deploy without user authority
        """),
        encoding="utf-8",
    )

    # .jarvis/memory/active/
    mem_active = root / ".jarvis" / "memory" / "active"
    mem_active.mkdir(parents=True)

    # A sample memory record
    (mem_active / "MEM-TEST-001.md").write_text(
        textwrap.dedent("""\
            ---
            id: MEM-TEST-001
            type: user-preference
            status: active
            source: user-statement
            confidence: 0.90
            authority: user-explicit
            approval: explicit
            actor: user
            scope: global
            created: "2026-09-11"
            valid_from: "2026-09-11"
            valid_until: "2027-09-11"
            supersedes: ""
            related:
              - MEM-TEST-002
            ---

            The operator prefers concise responses with direct conclusions first.
        """),
        encoding="utf-8",
    )

    # .jarvis/personas/definitions/
    personas_def = root / ".jarvis" / "personas" / "definitions"
    personas_def.mkdir(parents=True)

    (personas_def / "security-architect.md").write_text(
        textwrap.dedent("""\
            ---
            id: persona.security-architect
            name: Security Architect
            type: persona
            status: active
            activation: on-demand
            domains:
              - security
              - threat-modeling
              - access-control
            ---

            A security architect who assumes hostile inputs.
        """),
        encoding="utf-8",
    )

    # Vault, council, src, tests, docs — empty anchors
    for name in ("vault", "council", "src", "tests", "docs"):
        (root / name).mkdir()

    return root


@pytest.fixture()
def workspace(tmp_root: Path):
    """Return a Workspace rooted at tmp_root."""
    from jarvis.io.workspace import Workspace
    return Workspace(tmp_root)


@pytest.fixture()
def identity_md_path(tmp_root: Path) -> Path:
    return tmp_root / ".jarvis" / "core" / "identity.md"

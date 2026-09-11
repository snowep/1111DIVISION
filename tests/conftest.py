"""Shared fixtures for JARVIS test suite."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest


@pytest.fixture
def tmp_definitions(tmp_path: Path) -> Path:
    """Create a temporary definitions directory with two valid personas."""
    defs = tmp_path / "definitions"
    defs.mkdir()

    (defs / "Alice.md").write_text(
        textwrap.dedent("""\
            ---
            id: persona.alice
            name: Alice
            type: specialist-persona
            status: active
            activation: explicit
            domains:
              - logic
              - mathematics
              - puzzles
            ---

            # Identity

            You are operating as Alice — a specialist in logic and mathematics.

            # Primary Perspective

            - formal reasoning
            - proof construction
            - pattern recognition
        """),
        encoding="utf-8",
    )

    (defs / "Bob.md").write_text(
        textwrap.dedent("""\
            ---
            id: persona.bob
            name: Bob
            type: historical-persona
            status: active
            activation: both
            domains:
              - strategy
              - leadership
              - logic
            ---

            # Identity

            You are operating as Bob — a strategic leader.

            # Primary Perspective

            - long-term thinking
            - resource allocation
            - team building
        """),
        encoding="utf-8",
    )

    # README should be skipped by the scanner
    (defs / "README.md").write_text("# Definitions\n", encoding="utf-8")

    return defs


@pytest.fixture
def tmp_definitions_with_bad(tmp_definitions: Path) -> Path:
    """Add a malformed definition to the good set."""
    (tmp_definitions / "Bad.md").write_text(
        textwrap.dedent("""\
            ---
            id: persona.bad
            name: Bad
            ---
        """),
        encoding="utf-8",
    )
    return tmp_definitions


@pytest.fixture
def tmp_empty_definitions(tmp_path: Path) -> Path:
    """An empty definitions directory."""
    defs = tmp_path / "empty_definitions"
    defs.mkdir()
    return defs

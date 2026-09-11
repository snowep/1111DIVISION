"""Tests for jarvis.persona.manager — scan, parse, validate, registry build."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.persona.manager import (
    ValidationError,
    _parse_frontmatter,
    scan_definitions,
    build_registry,
)
from jarvis.persona.models import (
    ActivationMode,
    PersonaRegistry,
    PersonaStatus,
    PersonaType,
)


# ---------------------------------------------------------------------------
# Frontmatter parser
# ---------------------------------------------------------------------------

class TestParseFrontmatter:
    """Unit tests for the YAML frontmatter parser."""

    def test_valid_frontmatter(self):
        raw = (
            "---\n"
            "id: persona.test\n"
            "name: Test\n"
            "type: specialist-persona\n"
            "status: active\n"
            "activation: explicit\n"
            "domains:\n"
            "  - alpha\n"
            "  - beta\n"
            "---\n\n"
            "# Identity\n\n"
            "Some body text.\n"
        )
        fm, body = _parse_frontmatter(raw)

        assert fm["id"] == "persona.test"
        assert fm["name"] == "Test"
        assert fm["type"] == "specialist-persona"
        assert fm["status"] == "active"
        assert fm["activation"] == "explicit"
        assert fm["domains"] == ["alpha", "beta"]
        assert "# Identity" in body
        assert "Some body text." in body
        assert "---" not in body

    def test_no_frontmatter(self):
        raw = "# Just a heading\n\nNo frontmatter here.\n"
        fm, body = _parse_frontmatter(raw)
        assert fm == {}
        assert body == raw

    def test_empty_domains_list(self):
        raw = (
            "---\n"
            "id: persona.empty\n"
            "name: Empty\n"
            "type: specialist-persona\n"
            "status: active\n"
            "activation: explicit\n"
            "domains:\n"
            "---\n\n"
            "Body.\n"
        )
        fm, body = _parse_frontmatter(raw)
        assert fm["domains"] == []

    def test_single_domain(self):
        raw = (
            "---\n"
            "id: persona.one\n"
            "name: One\n"
            "type: specialist-persona\n"
            "status: active\n"
            "activation: explicit\n"
            "domains:\n"
            "  - alpha\n"
            "---\n\n"
            "Body.\n"
        )
        fm, _ = _parse_frontmatter(raw)
        assert fm["domains"] == ["alpha"]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestValidateDefinition:
    """Unit tests for frontmatter validation."""

    def test_valid_minimal(self):
        """Should not raise."""
        fm = {
            "id": "persona.x",
            "name": "X",
            "type": "specialist-persona",
            "status": "active",
            "activation": "explicit",
            "domains": ["logic"],
        }
        # Importing validate_definition would be cleaner but it raises on error
        # so "not raising" IS the test.
        from jarvis.persona.manager import validate_definition
        validate_definition(fm, "test.md")

    def test_missing_id(self):
        from jarvis.persona.manager import validate_definition
        fm = {
            "name": "X",
            "type": "specialist-persona",
            "status": "active",
            "activation": "explicit",
            "domains": ["logic"],
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_definition(fm, "test.md")
        assert exc_info.value.field == "id"

    def test_missing_name(self):
        from jarvis.persona.manager import validate_definition
        fm = {
            "id": "persona.x",
            "type": "specialist-persona",
            "status": "active",
            "activation": "explicit",
            "domains": ["logic"],
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_definition(fm, "test.md")
        assert exc_info.value.field == "name"

    def test_invalid_status(self):
        from jarvis.persona.manager import validate_definition
        fm = {
            "id": "persona.x",
            "name": "X",
            "type": "specialist-persona",
            "status": "deleted",
            "activation": "explicit",
            "domains": ["logic"],
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_definition(fm, "test.md")
        assert exc_info.value.field == "status"
        assert "deleted" in exc_info.value.message

    def test_invalid_activation(self):
        from jarvis.persona.manager import validate_definition
        fm = {
            "id": "persona.x",
            "name": "X",
            "type": "specialist-persona",
            "status": "active",
            "activation": "automatic",
            "domains": ["logic"],
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_definition(fm, "test.md")
        assert exc_info.value.field == "activation"

    def test_invalid_type(self):
        from jarvis.persona.manager import validate_definition
        fm = {
            "id": "persona.x",
            "name": "X",
            "type": "robot-persona",
            "status": "active",
            "activation": "explicit",
            "domains": ["logic"],
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_definition(fm, "test.md")
        assert exc_info.value.field == "type"

    def test_empty_domains(self):
        from jarvis.persona.manager import validate_definition
        fm = {
            "id": "persona.x",
            "name": "X",
            "type": "specialist-persona",
            "status": "active",
            "activation": "explicit",
            "domains": [],
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_definition(fm, "test.md")
        assert exc_info.value.field == "domains"

    def test_candidate_status_not_blocked_by_validation(self):
        """candidate is a valid status value — activation checks activatable, not validation."""
        from jarvis.persona.manager import validate_definition
        fm = {
            "id": "persona.x",
            "name": "X",
            "type": "specialist-persona",
            "status": "candidate",
            "activation": "explicit",
            "domains": ["logic"],
        }
        validate_definition(fm, "test.md")  # should not raise


# ---------------------------------------------------------------------------
# Scan & Registry
# ---------------------------------------------------------------------------

class TestScanDefinitions:
    """Integration tests for scanning a definitions directory."""

    def test_scan_valid_directory(self, tmp_definitions: Path):
        registry, errors = scan_definitions(tmp_definitions)

        assert len(errors) == 0
        assert registry.count == 2  # README skipped
        assert registry.get("persona.alice") is not None
        assert registry.get("persona.bob") is not None

    def test_scan_skips_readme(self, tmp_definitions: Path):
        registry, _ = scan_definitions(tmp_definitions)
        # README.md should not be in the registry
        all_names = [p.name for p in registry.personas.values()]
        assert "Readme" not in all_names
        assert "Definitions" not in all_names

    def test_scan_empty_directory(self, tmp_empty_definitions: Path):
        registry, errors = scan_definitions(tmp_empty_definitions)
        assert registry.count == 0
        assert errors == []

    def test_scan_nonexistent_directory(self, tmp_path: Path):
        registry, errors = scan_definitions(tmp_path / "nope")
        assert registry.count == 0
        assert errors == []

    def test_scan_with_bad_definitions(self, tmp_definitions_with_bad: Path):
        registry, errors = scan_definitions(tmp_definitions_with_bad)

        # Good ones still loaded
        assert registry.count == 2
        assert registry.get("persona.alice") is not None
        assert registry.get("persona.bob") is not None

        # Bad one reported
        assert len(errors) == 1
        assert "Bad.md" in errors[0].path

    def test_build_registry_strict(self, tmp_definitions_with_bad: Path):
        """build_registry raises on first error."""
        with pytest.raises(ValidationError):
            build_registry(tmp_definitions_with_bad)

    def test_build_registry_clean(self, tmp_definitions: Path):
        """build_registry succeeds on clean directory."""
        registry = build_registry(tmp_definitions)
        assert registry.count == 2


# ---------------------------------------------------------------------------
# Registry model behavior
# ---------------------------------------------------------------------------

class TestPersonaRegistry:
    """Tests for PersonaRegistry query methods."""

    def _make_registry(self) -> PersonaRegistry:
        from jarvis.persona.models import PersonaDefinition
        r = PersonaRegistry()
        r.add(PersonaDefinition(
            id="persona.a", name="A", type=PersonaType.SPECIALIST,
            status=PersonaStatus.ACTIVE, activation=ActivationMode.EXPLICIT,
            domains=("alpha", "beta"),
        ))
        r.add(PersonaDefinition(
            id="persona.b", name="B", type=PersonaType.HISTORICAL,
            status=PersonaStatus.ACTIVE, activation=ActivationMode.BOTH,
            domains=("beta", "gamma"),
        ))
        r.add(PersonaDefinition(
            id="persona.c", name="C", type=PersonaType.SPECIALIST,
            status=PersonaStatus.CANDIDATE, activation=ActivationMode.EXPLICIT,
            domains=("alpha",),
        ))
        return r

    def test_get_existing(self):
        r = self._make_registry()
        assert r.get("persona.a") is not None
        assert r.get("persona.a").name == "A"

    def test_get_missing(self):
        r = self._make_registry()
        assert r.get("persona.z") is None

    def test_activatable_excludes_candidate(self):
        r = self._make_registry()
        active = r.activatable()
        ids = {p.id for p in active}
        assert "persona.a" in ids
        assert "persona.b" in ids
        assert "persona.c" not in ids  # candidate

    def test_find_by_name_exact(self):
        r = self._make_registry()
        found = r.find_by_name("A")
        assert found is not None
        assert found.id == "persona.a"

    def test_find_by_name_case_insensitive(self):
        r = self._make_registry()
        found = r.find_by_name("b")
        assert found is not None
        assert found.id == "persona.b"

    def test_find_by_name_missing(self):
        r = self._make_registry()
        assert r.find_by_name("Z") is None

    def test_find_by_domain(self):
        r = self._make_registry()
        scored = r.find_by_domain({"alpha"})
        ids = [p.id for p, _ in scored]
        # Both A and C have alpha, but C is candidate so excluded
        assert "persona.a" in ids
        assert "persona.c" not in ids

    def test_count(self):
        r = self._make_registry()
        assert r.count == 3

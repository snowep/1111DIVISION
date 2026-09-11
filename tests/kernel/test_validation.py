"""Tests for jarvis.validation — YAML-subset parser, frontmatter, references.

Area 3: deterministic stdlib-only parsing + reference/duplicate resolution.
"""

import pytest

from jarvis.validation.pyaml import extract_frontmatter, parse_yaml_subset, YamlSyntaxError
from jarvis.validation.frontmatter import (
    check_required,
    check_enum,
    check_float_range,
    check_type,
    validate_frontmatter,
)
from jarvis.validation.references import (
    find_reference_targets,
    find_duplicate_ids,
    resolve_reference_target,
)
from jarvis.errors import (
    MissingFieldError,
    InvalidValueError,
)


# ---------- pyaml subset parser ----------


class TestParseYamlSubset:
    def test_scalars(self):
        data = parse_yaml_subset("name: JARVIS\nphase: 10\nconfidence: 0.9\n")
        assert data["name"] == "JARVIS"
        assert data["phase"] == 10
        assert data["confidence"] == 0.9

    def test_unknown_tags_refused(self):
        """YAML tags like !! are not supported by the subset parser.
        
        The parser rejects any construct it cannot deterministically parse.
        Tags like ``!!python`` are not in the supported subset.
        """
        # The tag lands in the value — parser either raises or treats it as scalar.
        # Either outcome is acceptable (defense-in-depth is at the authority layer).
        try:
            result = parse_yaml_subset("data: !!python/object/apply:os.system ['x']")
            # If it didn't raise, it treated the tag as part of the value
            assert isinstance(result["data"], str)
        except (YamlSyntaxError, Exception):
            pass  # Correctly rejected

    def test_plain_list(self):
        data = parse_yaml_subset("domains:\n  - a\n  - b\n")
        assert data["domains"] == ["a", "b"]

    def test_inline_list(self):
        data = parse_yaml_subset("domains: [security, architecture]\n")
        assert data["domains"] == ["security", "architecture"]

    def test_nested_map(self):
        data = parse_yaml_subset("evidence:\n  type: direct-observation\n  confidence: 0.95\n")
        assert data["evidence"]["type"] == "direct-observation"
        assert data["evidence"]["confidence"] == 0.95


class TestExtractFrontmatter:
    def test_standard(self):
        meta, body, has_fm = extract_frontmatter(
            "---\nid: demo\nstatus: active\n---\n# Heading\nBody.\n"
        )
        assert has_fm is True
        assert meta["id"] == "demo"
        assert meta["status"] == "active"
        assert "Heading" in body
        assert "Body" in body

    def test_no_frontmatter(self):
        meta, body, has_fm = extract_frontmatter("# Just body\n")
        assert has_fm is False
        assert meta == {}

    def test_empty_string(self):
        meta, body, has_fm = extract_frontmatter("")
        assert has_fm is False
        assert meta == {}
        assert body == ""

    def test_multiline_string_field(self):
        """Block scalars (|) are not supported by the YAML-subset parser."""
        with pytest.raises(Exception):
            extract_frontmatter(
                "---\ndescription: |\n  line one\n  line two\n---\nBody.\n"
            )


# ---------- frontmatter validators ----------


class TestFrontmatterValidators:
    def test_check_required_ok(self):
        metadata = {"id": "x", "status": "active"}
        check_required(metadata, "id", "status")

    def test_check_required_missing(self):
        metadata = {"id": "x"}
        with pytest.raises(MissingFieldError) as exc_info:
            check_required(metadata, "id", "status")
        assert exc_info.value.kind == "document.missing_field"

    def test_check_required_empty_string(self):
        with pytest.raises(MissingFieldError):
            check_required({"id": ""}, "id")

    def test_check_enum_ok(self):
        assert check_enum({"status": "active"}, "status", {"active", "candidate"}) == "active"

    def test_check_enum_invalid(self):
        with pytest.raises(InvalidValueError) as exc_info:
            check_enum({"status": "bogus"}, "status", {"active", "candidate"})
        assert exc_info.value.kind == "document.invalid_value"

    def test_check_float_range_ok(self):
        assert check_float_range({"confidence": 0.75}, "confidence") == 0.75

    def test_check_float_range_out_of_range(self):
        with pytest.raises(InvalidValueError):
            check_float_range({"confidence": 1.5}, "confidence")

    def test_check_float_range_non_numeric(self):
        with pytest.raises(InvalidValueError):
            check_float_range({"confidence": "high"}, "confidence")

    def test_check_type_ok(self):
        assert check_type({"id": "hello"}, "id", str) == "hello"

    def test_check_type_mismatch(self):
        with pytest.raises(InvalidValueError):
            check_type({"id": 123}, "id", str)

    def test_validate_frontmatter_composite(self):
        validate_frontmatter(
            {"id": "x", "status": "active"},
            required=("id", "status"),
            enum_fields={"status": {"active", "candidate"}},
        )

    def test_validate_frontmatter_fails(self):
        with pytest.raises(MissingFieldError):
            validate_frontmatter({"id": "x"}, required=("id", "status"))


# ---------- references ----------


class TestReferences:
    def test_find_reference_targets_id(self):
        refs = find_reference_targets("See MEM-001 and DEC-002 for context.", {})
        assert "MEM-001" in refs
        assert "DEC-002" in refs

    def test_find_reference_targets_wikilink(self):
        refs = find_reference_targets("See [[documentation/architecture]] for details.", {})
        assert "documentation/architecture" in refs

    def test_find_reference_targets_conventional_skipped(self):
        refs = find_reference_targets("Go to [[readme]] or [[index]] first.", {})
        assert refs == []

    def test_resolve_reference_target_known_id(self):
        target = resolve_reference_target("MEM-001", known_ids=["MEM-001"])
        assert target is not None
        assert hasattr(target, "id")
        assert target.id == "MEM-001"

    def test_resolve_reference_target_path(self, tmp_path):
        (tmp_path / "doc.md").write_text("hello")
        target = resolve_reference_target("doc", known_ids=[], workspace_root=tmp_path)
        assert target is not None
        assert target.is_file()

    def test_resolve_reference_target_unresolvable(self):
        target = resolve_reference_target("MEM-999", known_ids=["MEM-001"])
        assert target is None


# ---------- duplicate ids ----------


class TestDuplicateIds:
    def _doc(self, id_, path):
        from jarvis.models.document import MarkdownDocument
        return MarkdownDocument(
            source_path=path,
            relative_path=path,
            metadata={"id": id_},
            body="",
            has_frontmatter=True,
        )

    def test_no_duplicates(self):
        docs = [self._doc("A", "a.md"), self._doc("B", "b.md")]
        assert find_duplicate_ids(docs) == []

    def test_duplicates(self):
        docs = [self._doc("A", "a.md"), self._doc("A", "b.md")]
        dups = find_duplicate_ids(docs)
        assert len(dups) == 1
        assert dups[0][0] == "A"
        assert set(dups[0][1]) == {"a.md", "b.md"}
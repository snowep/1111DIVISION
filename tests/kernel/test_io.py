"""Tests for jarvis.io — workspace resolver + read/write boundary.

Area 4: path confinement, traversal rejection, anchors, read/write gates.
"""

import pytest

from jarvis.errors import (
    PathEscapeError,
    PathNotFoundError,
    UnknownAnchorError,
)
from jarvis.io.workspace import Workspace, detect_repository_root
from jarvis.io.boundary import (
    ReadBoundary,
    ReadOnlyBoundary,
    WriteBoundary,
    FullyMutableBoundary,
    OperationContext,
)


# ---------- workspace resolver ----------


class TestWorkspace:
    def test_root_detection(self, tmp_root):
        root = detect_repository_root(tmp_root)
        assert root == tmp_root

    def test_root_detection_from_nested(self, tmp_root):
        nested = tmp_root / ".jarvis" / "core"
        root = detect_repository_root(nested)
        assert root == tmp_root

    def test_no_git_raises(self, tmp_path):
        with pytest.raises(PathNotFoundError):
            detect_repository_root(tmp_path)

    def test_resolve_relative(self, workspace, tmp_root):
        resolved = workspace.resolve("vault/note.md")
        assert resolved == (tmp_root / "vault" / "note.md").resolve()

    def test_resolve_absolute_inside(self, workspace, tmp_root):
        resolved = workspace.resolve(tmp_root / "docs" / "README.md")
        assert resolved == (tmp_root / "docs" / "README.md").resolve()

    def test_resolve_traversal_rejected(self, workspace):
        with pytest.raises(PathEscapeError):
            workspace.resolve("../outside.md")

    def test_resolve_absolute_outside_rejected(self, workspace, tmp_path):
        outside = tmp_path / "other" / "file.md"
        with pytest.raises(PathEscapeError):
            workspace.resolve(outside)

    def test_resolve_empty_rejected(self, workspace):
        with pytest.raises(PathEscapeError):
            workspace.resolve("")

    def test_resolve_tilde_rejected(self, workspace):
        with pytest.raises(PathEscapeError):
            workspace.resolve("~/escape.md")

    def test_anchor_known(self, workspace, tmp_root):
        assert workspace.anchor("vault") == (tmp_root / "vault").resolve()

    def test_anchor_unknown(self, workspace):
        with pytest.raises(UnknownAnchorError):
            workspace.anchor("no-such-anchor")

    def test_conventions(self, workspace, tmp_root):
        assert workspace.core() == (tmp_root / ".jarvis" / "core").resolve()
        assert workspace.vault() == (tmp_root / "vault").resolve()
        assert workspace.council() == (tmp_root / "council").resolve()

    def test_resolve_read_missing(self, workspace):
        with pytest.raises(PathNotFoundError):
            workspace.resolve_read("vault/does-not-exist.md")

    def test_resolve_read_present(self, workspace, tmp_root):
        p = workspace.resolve_read(".jarvis/core/constitution.md")
        assert p.is_file()
        assert "Constitution" in p.read_text(encoding="utf-8")

    def test_anchors_dict(self, workspace):
        anchors = workspace.anchors()
        assert ".jarvis" in anchors
        assert "vault" in anchors


# ---------- read boundary ----------


class TestReadBoundary:
    def test_read_file(self, workspace):
        rb = ReadBoundary(workspace)
        content = rb.read_file(".jarvis/core/constitution.md")
        assert "Constitution" in content

    def test_read_missing_file_raises(self, workspace):
        rb = ReadBoundary(workspace)
        with pytest.raises(PathNotFoundError):
            rb.read_file("nope.md")

    def test_read_directory_rejected(self, workspace):
        rb = ReadBoundary(workspace)
        with pytest.raises(Exception):
            rb.read_file("vault")

    def test_list_files(self, workspace):
        rb = ReadBoundary(workspace)
        files = rb.list_files(".jarvis/core")
        names = [f.name for f in files]
        assert "constitution.md" in names

    def test_is_valid_target(self, workspace):
        rb = ReadBoundary(workspace)
        assert rb.is_valid_target("vault/a.md")
        assert not rb.is_valid_target("../escape.md")


# ---------- write boundary ----------


class TestWriteBoundary:
    def test_write_requires_user_authority(self, workspace):
        from jarvis.io.boundary import WriteBoundary
        wb = WriteBoundary(workspace)
        result = wb.write(
            "# New",
            "vault/new.md",
            authority="system",
            actor="jarvis",
        )
        assert result.success is False
        assert result.error_codes == ("operation.authority_denied",)

    def test_write_allowed_with_user_authority(self, workspace):
        wb = WriteBoundary(workspace)
        result = wb.write(
            "# New\n\nBody.",
            "vault/safe.md",
            authority="user-explicit",
            actor="user",
        )
        assert result.success is True
        assert (workspace.root / "vault" / "safe.md").exists()
        # cleanup
        (workspace.root / "vault" / "safe.md").unlink()

    def test_write_outside_root_refused(self, workspace, tmp_path):
        wb = WriteBoundary(workspace)
        outside = tmp_path / "escape.md"
        result = wb.write("evil", str(outside), authority="user-explicit")
        assert result.success is False

    def test_write_with_extra_validator(self, workspace):
        wb = WriteBoundary(workspace)

        def no_uppercase(context: OperationContext, path) -> tuple[bool, str]:
            return False, "validator refuses"

        result = wb.write(
            "# X",
            "vault/blocked.md",
            no_uppercase,
            authority="user-explicit",
        )
        assert result.success is False
        assert result.error_codes == ("operation.authority_denied",)

    def test_write_failed_os_error(self, workspace):
        wb = WriteBoundary(workspace)
        # Attempt to write into a path whose parent is a file
        target = workspace.root / "vault" / "blocked-parent"
        target.write_text("i am a file")
        result = wb.write("# X", str(target / "child.md"), authority="user-explicit")
        assert result.success is False
        assert result.error_codes == ("operation.mutation_forbidden",)


# ---------- read-only boundary ----------


class TestReadOnlyBoundary:
    def test_write_refused(self, workspace):
        rob = ReadOnlyBoundary(workspace)
        result = rob.write("# X", "vault/x.md", authority="user-explicit")
        assert result.success is False
        assert result.error_codes == ("operation.mutation_forbidden",)


# ---------- fully mutable boundary ----------


class TestFullyMutableBoundary:
    def test_refuses_git(self, workspace):
        fmb = FullyMutableBoundary(workspace)
        result = fmb.write("# x", ".git/config", authority="user-explicit")
        assert result.success is False

    def test_applies_when_authorized(self, workspace):
        fmb = FullyMutableBoundary(workspace)
        result = fmb.write("# x", "docs/note.md", authority="user-explicit")
        assert result.success is True
        target = workspace.root / "docs" / "note.md"
        assert target.exists()
        target.unlink()
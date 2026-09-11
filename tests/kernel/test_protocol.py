"""Tests for jarvis.validation.protocol — authority boundary.

Area 6: mutations to protected .jarvis/core files are gated; workspace
mutations are allowed; external paths are denied.
"""

import pytest

from jarvis.validation.protocol import authority_is_valid, constitution_check
from jarvis.errors import AuthorityDeniedError, PathEscapeError


class TestAuthorityIsValid:
    def test_workspace_file_allowed(self, workspace):
        assert authority_is_valid(workspace, "docs/note.md") is True

    def test_core_whitelisted_allowed(self, workspace):
        assert authority_is_valid(workspace, ".jarvis/core/constitution.md") is True
        assert authority_is_valid(workspace, ".jarvis/core/identity.md") is True
        assert authority_is_valid(workspace, ".jarvis/core/world-model.md") is True

    def test_core_not_whitelisted_denied(self, workspace):
        with pytest.raises(AuthorityDeniedError):
            authority_is_valid(workspace, ".jarvis/core/private-secrets.md")

    def test_outside_workspace_denied(self, workspace, tmp_path):
        outside = tmp_path / "escape.md"
        with pytest.raises(AuthorityDeniedError):
            authority_is_valid(workspace, str(outside))

    def test_path_escape_denied(self, workspace):
        with pytest.raises(AuthorityDeniedError):
            authority_is_valid(workspace, "../escape.md")

    def test_constitution_check_alias(self, workspace):
        assert constitution_check(workspace, "docs/note.md") is True
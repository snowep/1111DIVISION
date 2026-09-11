from __future__ import annotations

import pytest

from jarvis.docstore.store import DocumentStore


@pytest.fixture
def store(tmp_path):
    return DocumentStore(tmp_path / ".jarvis")
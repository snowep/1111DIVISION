"""JARVIS runtime kernel — validation package.

Pure, deterministic, dependency-free validation:

- ``pyaml``  — a minimal deterministic YAML-subset parser (stdlib only).
- ``frontmatter`` — required-field / enum / type checkers for Markdown frontmatter.
- ``status`` — the canonical state-machine status vocabulary.
- ``references`` — resolution + duplicate/broken-reference detection.
"""

from jarvis.validation.frontmatter import (
    check_enum,
    check_float_range,
    check_required,
    check_type,
    validate_frontmatter,
)
from jarvis.validation.status import (
    ACTOR_VALUES,
    AUTHORITY_VALUES,
    APPROVAL_VALUES,
    MEMORY_TYPES,
    STATE_STATUS_VALUES,
    VALID_STATUS_VALUES,
    StatusVocabulary,
)
from jarvis.validation.references import (
    find_duplicate_ids,
    find_reference_targets,
    find_unresolved_references,
    resolve_reference_target,
    validate_no_duplicate_ids,
    validate_references_resolve,
)

__all__ = [
    "pyaml",
    "check_required",
    "check_type",
    "check_enum",
    "check_float_range",
    "validate_frontmatter",
    "StatusVocabulary",
    "VALID_STATUS_VALUES",
    "STATE_STATUS_VALUES",
    "ACTOR_VALUES",
    "AUTHORITY_VALUES",
    "APPROVAL_VALUES",
    "MEMORY_TYPES",
    "find_duplicate_ids",
    "find_reference_targets",
    "find_unresolved_references",
    "resolve_reference_target",
    "validate_no_duplicate_ids",
    "validate_references_resolve",
]
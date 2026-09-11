"""Bounded runtime operations for the JARVIS kernel.

Each operation is:
- deterministic (same inputs → same outputs)
- bounded (no network, no subprocess, no sleep)
- evidenced (every result carries evidence/provenance)
- validated (always runs through the authority boundary before mutation)
"""

from jarvis.runtime.operations import OperationList

__all__ = ["execute_read_document", "execute_load_identity", "execute_build_context",
           "execute_validate_memory", "execute_run_gate",
           "OperationList"]
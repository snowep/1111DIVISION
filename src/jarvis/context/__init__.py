"""JARVIS runtime kernel — context assembly.

Builds the exact 9-layer runtime context in the architecture order:
platform constraints → constitution → system prompt → world model →
relevant memory → skills → task context → persona overlay → user request.

The builder enforces two contracts:

1. **Layer ordering**: layer 1 outranks layer 2, etc.  If a lower layer
   (say persona) tries to override a value already set by a higher layer
   (constitution), the builder raises ``LayerOverrideError``.

2. **Value precedence is structured**: raw content is stored in each
   layer's ``content`` field, but actual key–value changes go through
   ``assertions``.  This makes precedence deterministic and inspectable.
"""

from jarvis.context.builder import ContextBuilder

__all__ = ["ContextBuilder"]
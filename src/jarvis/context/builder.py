"""Context builder: assembles the deterministic prompt context.

Ordering (CANONICAL — lower layers never override higher ones):

    0  platform / system constraints       (highest)
    1  constitution (rules that govern JARVIS)
    2  system prompt (shape of JARVIS)
    3  world model  (derived, rebuildable)
    4  relevant memory (vault notes, importance-ranked)
    5  skills        (registered, active)
    6  task context  (current objective)
    7  persona overlay (reasoning persona, if any)
    8  user request  (the actual instruction)  (lowest)

The rule is enforced two ways:
- ``build_context`` lays layers in priority order (high first).
- ``apply_override`` refuses to let a lower layer overwrite a higher one
  (raises ContextError), giving the caller an inspectable guarantee.

The assembled context is deterministic: identical inputs -> identical
output (no timestamps sneak into the priority structure; metadata may
carry timestamps as provenance but never as ordering keys).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from jarvis.errors import ContextError

# Canonical priority order, index 0 = highest.
LAYER_PRIORITY: tuple[str, ...] = (
    "platform",
    "constitution",
    "system",
    "world_model",
    "memory",
    "skills",
    "task",
    "persona",
    "user",
)

# Lower-bound index that may NOT be overridden by a given layer.
# Any layer may override layers BELOW it (higher index), never above.


def _layer_index(layer: str) -> int:
    if layer not in LAYER_PRIORITY:
        raise ContextError(f"unknown context layer: {layer!r}")
    return LAYER_PRIORITY.index(layer)


@dataclass
class ContextLayer:
    """One named layer of assembled context."""

    name: str
    content: str
    priority: int  # 0 = highest
    count: int = 0  # number of source items folded into this layer
    provenance: list[str] = field(default_factory=list)


@dataclass
class AssembledContext:
    """The fully assembled, ordered context."""

    layers: list[ContextLayer]

    @property
    def text(self) -> str:
        """Join layers by bound priority, highest first."""
        parts: list[str] = []
        for i in range(len(LAYER_PRIORITY)):
            for layer in self.layers:
                if layer.priority == i and layer.content.strip():
                    parts.append(f"[{layer.name}]\n{layer.content.strip()}")
        return "\n\n".join(parts)

    def get(self, name: str) -> Optional[ContextLayer]:
        for layer in self.layers:
            if layer.name == name:
                return layer
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "layers": [
                {
                    "name": l.name,
                    "priority": l.priority,
                    "count": l.count,
                    "characters": len(l.content),
                    "provenance": l.provenance,
                }
                for l in sorted(self.layers, key=lambda x: x.priority)
            ]
        }


class ContextBuilder:
    """Stack + resolve context layers deterministically."""

    def __init__(self) -> None:
        self._layers: dict[str, ContextLayer] = {}

    # ----------------------------------------------------------------- add
    def add(self, name: str, content: str, *, count: int = 0, provenance: Optional[list[str]] = None) -> None:
        layer = ContextLayer(
            name=name,
            content=content,
            priority=_layer_index(name),
            count=count,
            provenance=list(provenance or []),
        )
        self._layers[name] = layer

    # -------------------------------------------------------------- merge
    def apply_override(self, name: str, content: str, *, caller: Optional[str] = None, count: int = 0, provenance: Optional[list[str]] = None) -> None:
        """Override an existing layer, enforcing the priority invariant.

        The rule: a lower layer (higher priority index, e.g. 'user') may
        NEVER push content into a higher layer (lower index, e.g.
        'platform'). ``caller`` names the layer performing the write.

        - caller=None: the builder/assembler itself — may refresh any layer.
        - caller=X:    X's priority index must be <= the target's index
                       (X is equal-or-higher priority); otherwise the write
                       is refused with ContextError.
        """
        if name not in self._layers:
            raise ContextError(f"cannot override unknown layer {name!r}")
        new_prio = _layer_index(name)
        if caller is not None:
            caller_prio = _layer_index(caller)
            if caller_prio > new_prio:
                raise ContextError(
                    f"priority violation: layer '{caller}' (priority {caller_prio}) "
                    f"attempted to override higher layer '{name}' (priority {new_prio}) — "
                    f"lower layers never override higher ones"
                )
        self._layers[name] = ContextLayer(
            name=name,
            content=content,
            priority=new_prio,
            count=count,
            provenance=list(provenance or []),
        )

    # -------------------------------------------------------------- get
    def get(self, name: str) -> Optional[ContextLayer]:
        """Return a stored layer without building the full context."""
        return self._layers.get(name)

    # ------------------------------------------------------------ build
    def build(self) -> AssembledContext:
        """Return layers in canonical priority order (0 first)."""
        ordered = sorted(self._layers.values(), key=lambda l: (l.priority, l.name))
        return AssembledContext(layers=ordered)
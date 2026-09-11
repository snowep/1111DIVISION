"""Runtime context model — the 9-layer prompt composition contract.

Encodes the architecture's priority rule (runtime-spec.md:
PLATFORM > CONSTITUTION > SYSTEM PROMPT > WORLD MODEL > MEMORY > SKILLS
> TASK > PERSONA > USER REQUEST) plus its single exception: the User
Request (layer 9) may override layers 4-8 for task-specific decisions,
but never layers 1-3.

Enforcement is structural: assertions (key → value) are stamped with the
layer that made them, and a lower-priority layer asserting a different
value for an already-claimed key is refused with ``LayerOverrideError``.
Raw layer *text* is inert — only structured assertions are enforced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from jarvis.errors import LayerOverrideError

# User Request may override layers in [4, 8] (task-specific decisions only).
USER_REQUEST_OVERRIDABLE_MIN = 4
USER_REQUEST_OVERRIDABLE_MAX = 8

# Layers 1-3 are immutable: platform constraints, constitution, system prompt.
IMMUTABLE_LAYER_NUMBERS = frozenset({1, 2, 3})

VALID_LAYER_RANGE = range(1, 10)

LAYER_NAMES = {
    1: "platform-constraints",
    2: "constitution",
    3: "system-prompt",
    4: "world-model",
    5: "memory",
    6: "skills",
    7: "task-context",
    8: "persona-overlay",
    9: "user-request",
}


@dataclass(frozen=True)
class ContextLayer:
    """One layer of the assembled runtime context.

    ``number`` is the architecture layer (1 = highest priority, 9 = lowest).
    ``content`` is the raw text of the layer.  ``immutable`` marks layers
    1-3 which no lower layer may override.
    """

    number: int
    name: str
    content: str = ""
    source: str = ""
    immutable: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.number not in VALID_LAYER_RANGE:
            raise ValueError(f"Layer number must be 1-9, got {self.number}")
        if self.name != LAYER_NAMES[self.number]:
            raise ValueError(
                f"Layer {self.number} must be named {LAYER_NAMES[self.number]!r}, "
                f"got {self.name!r}"
            )
        if self.number in IMMUTABLE_LAYER_NUMBERS:
            object.__setattr__(self, "immutable", True)

    def outranks(self, other: "ContextLayer") -> bool:
        """True if this layer has strictly higher priority (lower number)."""
        return self.number < other.number

    def can_override(self, other: "ContextLayer") -> bool:
        """Can this layer's assertion override ``other``'s assertion?

        Rules:
        - An immutable layer (1-3) can never be overridden.
        - User Request (9) may override layers 4-8 only.
        - Otherwise: higher priority (lower number) wins.
        """
        if other.immutable:
            return False
        # Layer 9 (User Request) special case: may override layers 4-8
        if self.number == 9:
            return (
                USER_REQUEST_OVERRIDABLE_MIN
                <= other.number
                <= USER_REQUEST_OVERRIDABLE_MAX
            )
        # Normal priority: lower number outranks higher number
        return self.number < other.number

    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "name": self.name,
            "content": self.content,
            "source": self.source,
            "immutable": self.immutable,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class LayerAssertion:
    """A structured value asserted by a specific context layer.

    ``key`` is a dotted path like ``"world_model.phase"`` or
    ``"identity.name"``.  The same key may be asserted by different layers;
    only differing values are conflicts.
    """

    key: str
    value: Any
    layer_number: int


@dataclass
class RuntimeContext:
    """The assembled runtime context: ordered layers + enforced assertions.

    ``layers`` is keyed by layer number (1-9).  ``assertions`` maps a
    dotted key to the most recent winning :class:`LayerAssertion`.
    """

    layers: dict[int, ContextLayer] = field(default_factory=dict)
    assertions: dict[str, LayerAssertion] = field(default_factory=dict)

    # -- layers -----------------------------------------------------------

    def add_layer(self, layer: ContextLayer) -> None:
        """Add (or replace) a context layer.

        Replacing the same layer number is allowed (rebuild); a different
        layer cannot be inserted at the same number.
        """
        existing = self.layers.get(layer.number)
        if existing is not None and existing.name != layer.name:
            raise ValueError(
                f"Layer {layer.number} already registered as {existing.name!r}, "
                f"cannot register {layer.name!r}"
            )
        self.layers[layer.number] = layer

    def get_layer(self, number: int) -> Optional[ContextLayer]:
        return self.layers.get(number)

    def ordered_layers(self) -> list[ContextLayer]:
        """Layers sorted by priority (ascending number)."""
        return [self.layers[n] for n in sorted(self.layers)]

    @property
    def layer_count(self) -> int:
        return len(self.layers)

    # -- assertions -------------------------------------------------------

    def assert_value(self, key: str, value: Any, layer_number: int) -> LayerAssertion:
        """Structured precedence enforcement.

        Record that ``layer_number`` asserts ``key == value``.

        Raises
        ------
        LayerOverrideError
            If a lower-priority layer asserts a *different* value for a key
            already held by a higher-priority layer, or a layer attempts to
            override an immutable assertion.
        """
        if layer_number not in VALID_LAYER_RANGE:
            raise ValueError(f"Layer number must be 1-9, got {layer_number}")

        existing = self.assertions.get(key)
        if existing is not None and existing.value != value:
            incoming = ContextLayer(
                number=layer_number,
                name=LAYER_NAMES[layer_number],
            )
            holder = ContextLayer(
                number=existing.layer_number,
                name=LAYER_NAMES[existing.layer_number],
            )
            if not incoming.can_override(holder):
                raise LayerOverrideError(
                    f"Layer {layer_number} ({LAYER_NAMES[layer_number]}) tried to "
                    f"override {key} = {existing.value!r} asserted by layer "
                    f"{existing.layer_number} ({LAYER_NAMES[existing.layer_number]}). "
                    f"The architecture forbids lower layers overriding higher layers.",
                    path=key,
                    code="precedence",
                )
            # Legal override: replace the winner.
            self.assertions[key] = LayerAssertion(key, value, layer_number)
            return self.assertions[key]

        if existing is None:
            self.assertions[key] = LayerAssertion(key, value, layer_number)
        # identical value: keep the higher-priority holder as-is
        return self.assertions[key]

    def current_value(self, key: str) -> Any:
        """Value of the winning assertion for *key*, or None."""
        assertion = self.assertions.get(key)
        return None if assertion is None else assertion.value

    def assertion_of(self, key: str) -> Optional[LayerAssertion]:
        return self.assertions.get(key)

    def as_assertion_dict(self) -> dict:
        return {k: a.value for k, a in self.assertions.items()}

    # -- assembly ---------------------------------------------------------

    def assemble_text(self) -> str:
        """Concatenate layer content in priority order into one context block."""
        blocks = []
        for layer in self.ordered_layers():
            blocks.append(
                f"<LAYER {layer.number} — {layer.name}"
                + (" [immutable]" if layer.immutable else "")
                + ">\n"
                + (layer.content or "(empty)")
            )
        return "\n\n".join(blocks)

    def to_dict(self) -> dict:
        return {
            "layers": {str(n): l.to_dict() for n, l in self.layers.items()},
            "assertions": {
                k: {"value": a.value, "layer": a.layer_number}
                for k, a in self.assertions.items()
            },
        }
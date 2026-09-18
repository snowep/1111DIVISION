"""
Version helpers for the ORION Evolution system.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Version:
    """Semantic version representation."""
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> "Version":
        match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", value.strip())
        if not match:
            raise ValueError(f"Invalid version: {value}")
        return cls(int(match.group(1)), int(match.group(2)), int(match.group(3)))

    def bump(self, kind: str = "patch") -> "Version":
        if kind == "major":
            return Version(self.major + 1, 0, 0)
        if kind == "minor":
            return Version(self.major, self.minor + 1, 0)
        if kind == "patch":
            return Version(self.major, self.minor, self.patch + 1)
        raise ValueError(f"Unknown version bump kind: {kind}")

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

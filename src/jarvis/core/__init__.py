"""core: JARVIS identity and authoritative configuration.

Only `.jarvis/core` is ever read as the identity source. Open WebUI
configuration and environment variables are never treated as identity.
"""
from jarvis.core.identity import Identity, load_identity

__all__ = ["Identity", "load_identity"]
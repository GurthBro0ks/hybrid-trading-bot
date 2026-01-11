"""STUB_ONLY: Compatibility shim for SHADOW runner import graph.

Must remain read-only and must not place orders or make authenticated network calls.
"""

from .stale_edge import BookTop, Decision, StaleEdgeStrategy

__all__ = ["BookTop", "Decision", "StaleEdgeStrategy"]

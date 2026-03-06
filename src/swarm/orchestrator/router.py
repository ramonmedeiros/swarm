from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Router:
    """
    Minimal rule-based router.

    Swap this out later for LLM-based routing or a learned policy.
    """

    def pick_agent(self, *, step: int) -> str:
        # Simple alternation: worker does generation, critic reviews.
        return "worker" if step % 2 == 0 else "critic"


from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass(frozen=True)
class AgentResult:
    output: str
    done: bool = False


class Agent(Protocol):
    name: str

    def run(self, *, task_input: str) -> AgentResult: ...


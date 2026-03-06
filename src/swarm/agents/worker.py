from __future__ import annotations

from dataclasses import dataclass

from ..llm import LLMClient
from .base import AgentResult


@dataclass(frozen=True)
class WorkerAgent:
    llm: LLMClient
    model: str
    name: str = "worker"

    def run(self, *, task_input: str) -> AgentResult:
        prompt = (
            "You are a helpful execution-focused agent.\n"
            "Produce the best possible answer to the user task.\n\n"
            f"Task:\n{task_input}\n"
        )
        text = self.llm.generate_text(prompt=prompt, model=self.model)
        # Not done by default; the orchestrator decides when to stop.
        return AgentResult(output=text, done=False)


from __future__ import annotations

from dataclasses import dataclass

from ..llm import LLMClient
from .base import AgentResult


@dataclass(frozen=True)
class CriticAgent:
    llm: LLMClient
    model: str
    name: str = "critic"

    def run(self, *, task_input: str) -> AgentResult:
        prompt = (
            "You are a critical reviewer.\n"
            "Review the proposed solution and suggest improvements.\n"
            "If the solution is already strong, respond with 'DONE' and a short reason.\n\n"
            f"Context:\n{task_input}\n"
        )
        text = self.llm.generate_text(prompt=prompt, model=self.model)
        done = text.strip().upper().startswith("DONE")
        return AgentResult(output=text, done=done)


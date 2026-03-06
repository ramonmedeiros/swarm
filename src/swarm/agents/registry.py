from __future__ import annotations

from dataclasses import dataclass

from ..llm import LLMClient
from .base import Agent
from .critic import CriticAgent
from .worker import WorkerAgent


@dataclass
class AgentRegistry:
    agents: dict[str, Agent]

    def get(self, name: str) -> Agent:
        return self.agents[name]

    def list(self) -> list[str]:
        return list(self.agents.keys())


def register_default_agents(*, llm: LLMClient, model: str) -> AgentRegistry:
    agents: dict[str, Agent] = {
        "worker": WorkerAgent(llm=llm, model=model),
        "critic": CriticAgent(llm=llm, model=model),
    }
    return AgentRegistry(agents=agents)


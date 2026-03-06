from __future__ import annotations

import uuid
from dataclasses import dataclass

from ..agents import AgentRegistry
from ..memory import MemoryStore
from .router import Router


@dataclass
class SwarmRunResult:
    task_id: str
    output: str
    trace: list[dict]


@dataclass
class Swarm:
    registry: AgentRegistry
    router: Router
    memory: MemoryStore
    max_steps: int = 6

    def run(self, *, task_input: str, max_steps: int | None = None) -> SwarmRunResult:
        task_id = str(uuid.uuid4())
        steps = max_steps if max_steps is not None else self.max_steps

        last_output = ""
        trace: list[dict] = []

        for step in range(steps):
            agent_name = self.router.pick_agent(step=step)
            agent = self.registry.get(agent_name)

            context = self._build_context(task_input=task_input, last_output=last_output)
            result = agent.run(task_input=context)

            item = {
                "step": step,
                "agent": agent_name,
                "output": result.output,
                "done": result.done,
            }
            self.memory.append(task_id=task_id, item=item)
            trace.append(item)

            last_output = result.output
            if result.done:
                break

        return SwarmRunResult(task_id=task_id, output=last_output, trace=trace)

    def _build_context(self, *, task_input: str, last_output: str) -> str:
        if not last_output:
            return task_input
        return (
            f"Original task:\n{task_input}\n\n"
            f"Previous agent output:\n{last_output}\n"
        )


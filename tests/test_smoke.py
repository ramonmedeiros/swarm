from __future__ import annotations

from swarm.agents import register_default_agents
from swarm.api.main import create_app
from swarm.memory import InMemoryStore
from swarm.orchestrator import Router, Swarm


class FakeLLM:
    def generate_text(self, *, prompt: str, model: str) -> str:
        if "critical reviewer" in prompt:
            return "DONE: Looks good."
        return "Draft answer."


def test_swarm_runs_and_stops_on_done() -> None:
    llm = FakeLLM()
    registry = register_default_agents(llm=llm, model="fake")
    swarm = Swarm(registry=registry, router=Router(), memory=InMemoryStore(), max_steps=6)

    result = swarm.run(task_input="Say hello", max_steps=4)
    assert result.trace[0]["agent"] == "worker"
    assert result.trace[1]["agent"] == "critic"
    assert result.output.startswith("DONE")


def test_api_healthz_boots_without_env() -> None:
    app = create_app(swarm=None)
    # No test client needed; just ensure route table is created.
    routes = {getattr(r, "path", None) for r in app.routes}
    assert "/healthz" in routes
    assert "/v1/tasks" in routes


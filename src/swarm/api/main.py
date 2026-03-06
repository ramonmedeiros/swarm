from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field, ValidationError

from ..agents import register_default_agents
from ..config import Settings, get_settings
from ..llm import GeminiClient
from ..logging import configure_logging
from ..memory import FilesystemMemoryStore
from ..orchestrator import Router, Swarm

logger = logging.getLogger("swarm.api")

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class TaskRequest(BaseModel):
    input: str = Field(min_length=1)
    max_steps: int | None = Field(default=None, ge=1, le=32)


class TaskResponse(BaseModel):
    task_id: str
    output: str
    trace: list[dict[str, Any]]


def _build_swarm(settings: Settings) -> Swarm:
    llm = GeminiClient(api_key=settings.gemini_api_key)
    registry = register_default_agents(llm=llm, model=settings.gemini_model)
    router = Router()
    memory = FilesystemMemoryStore(settings.swarm_memory_dir)
    return Swarm(registry=registry, router=router, memory=memory, max_steps=settings.swarm_max_steps)


def create_app(*, swarm: Swarm | None = None) -> FastAPI:
    app = FastAPI(title="epiminds-swarm", version="0.1.0")

    app.state.settings = None
    app.state.swarm = swarm

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        rid = request.headers.get("x-request-id") or str(uuid.uuid4())
        token = request_id_ctx.set(rid)
        try:
            response: Response = await call_next(request)
            response.headers["x-request-id"] = rid
            return response
        finally:
            request_id_ctx.reset(token)

    @app.on_event("startup")
    async def _startup() -> None:
        try:
            settings = get_settings()
        except ValidationError:
            # Allow booting without env for local dev/tests; task endpoint will error clearly.
            settings = None
        if settings is None:
            configure_logging("INFO")
            logger.warning("Missing GEMINI_API_KEY; /v1/tasks will be unavailable until configured")
            app.state.settings = None
            return

        configure_logging(settings.log_level)
        app.state.settings = settings
        if app.state.swarm is None:
            app.state.swarm = _build_swarm(settings)

    @app.get("/healthz")
    async def healthz() -> dict[str, Any]:
        s: Settings | None = app.state.settings
        return {
            "ok": True,
            "configured": s is not None,
            "model": getattr(s, "gemini_model", None),
        }

    @app.post("/v1/tasks", response_model=TaskResponse)
    async def create_task(payload: TaskRequest) -> TaskResponse:
        swarm_obj: Swarm | None = app.state.swarm
        if swarm_obj is None:
            raise HTTPException(
                status_code=503,
                detail="Swarm not configured. Set GEMINI_API_KEY (and optionally GEMINI_MODEL) and restart.",
            )

        result = swarm_obj.run(task_input=payload.input, max_steps=payload.max_steps)
        return TaskResponse(task_id=result.task_id, output=result.output, trace=result.trace)

    return app


app = create_app()


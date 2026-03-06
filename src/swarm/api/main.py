from __future__ import annotations

import asyncio
import json
import logging
import uuid
from contextvars import ContextVar
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost",
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
            "https://swarm-frontend-ecru.vercel.app/"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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

    def _memory_dir() -> Path:
        s: Settings | None = app.state.settings
        if s is None:
            raise HTTPException(
                status_code=503,
                detail="Settings not configured; memory directory unavailable.",
            )
        return Path(s.swarm_memory_dir).resolve()

    def _memory_file_list(root: Path) -> list[str]:
        if not root.exists():
            return []
        files: list[str] = []
        for p in sorted(root.rglob("*")):
            if p.is_file():
                try:
                    files.append(str(p.relative_to(root)))
                except ValueError:
                    continue
        return files

    async def _sse_memory_files(interval: float = 2.0) -> AsyncIterator[str]:
        root = _memory_dir()
        while True:
            files = _memory_file_list(root)
            yield f"data: {json.dumps(files)}\n\n"
            await asyncio.sleep(interval)

    @app.get("/v1/memory/files")
    async def stream_memory_files(interval: int = 2) -> StreamingResponse:
        """Stream available file paths in the memory directory via SSE. Rescans every `interval` seconds (1-60)."""
        interval = max(1, min(60, interval))
        return StreamingResponse(
            _sse_memory_files(interval=float(interval)),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.get("/v1/memory/content/{file_path:path}")
    async def get_memory_file_content(file_path: str) -> Response:
        """Return the content of a file inside the memory directory."""
        root = _memory_dir()
        if not root.exists():
            raise HTTPException(status_code=404, detail="Memory directory not found")
        resolved = (root / file_path).resolve()
        try:
            if not resolved.is_relative_to(root):
                raise HTTPException(status_code=403, detail="Path outside memory directory")
        except AttributeError:
            if not str(resolved).startswith(str(root)):
                raise HTTPException(status_code=403, detail="Path outside memory directory")
        if not resolved.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        content = resolved.read_text(encoding="utf-8")
        return Response(content=content, media_type="text/plain; charset=utf-8")

    return app


app = create_app()


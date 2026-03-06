from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from .store import MemoryStore

LOGS_DIR = "logs"
LONG_MEMORY_FILENAME = "MEMORY.md"


class FilesystemMemoryStore(MemoryStore):
    """OpenClaw-style filesystem memory: timestamped markdown logs + long-memory file."""

    def __init__(self, memory_dir: str | Path) -> None:
        self._memory_dir = Path(memory_dir).resolve()
        self._logs_dir = self._memory_dir / LOGS_DIR

    def _ensure_dirs(self) -> None:
        self._memory_dir.mkdir(parents=True, exist_ok=True)
        self._logs_dir.mkdir(parents=True, exist_ok=True)

    def _timestamp_filename(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d_T%H-%M-%S.md")

    def _item_to_markdown(self, task_id: str, item: dict) -> str:
        lines = [
            "---",
            f"task_id: {task_id}",
            f"step: {item.get('step', '')}",
            f"agent: {item.get('agent', '')}",
            f"done: {item.get('done', False)}",
            "---",
            "",
            "## Output",
            "",
            str(item.get("output", "")).strip(),
        ]
        return "\n".join(lines)

    def _parse_log_file(self, path: Path) -> tuple[str, dict] | None:
        text = path.read_text(encoding="utf-8")
        task_id_match = re.search(r"^task_id:\s*(.+)$", text, re.MULTILINE)
        if not task_id_match:
            return None
        task_id = task_id_match.group(1).strip()
        step_match = re.search(r"^step:\s*(.+)$", text, re.MULTILINE)
        agent_match = re.search(r"^agent:\s*(.+)$", text, re.MULTILINE)
        done_match = re.search(r"^done:\s*(.+)$", text, re.MULTILINE)
        output_match = re.search(r"## Output\s*\n+(.*)", text, re.DOTALL)
        step_s = step_match.group(1).strip() if step_match else 0
        try:
            step = int(step_s)
        except ValueError:
            step = 0
        agent = agent_match.group(1).strip() if agent_match else ""
        done_str = done_match.group(1).strip().lower() if done_match else "false"
        done = done_str in ("true", "1", "yes")
        output = output_match.group(1).strip() if output_match else ""
        return (
            task_id,
            {"step": step, "agent": agent, "output": output, "done": done},
        )

    def append(self, *, task_id: str, item: dict) -> None:
        self._ensure_dirs()
        path = self._logs_dir / self._timestamp_filename()
        path.write_text(
            self._item_to_markdown(task_id=task_id, item=item),
            encoding="utf-8",
        )

    def get(self, *, task_id: str) -> list[dict]:
        if not self._logs_dir.exists():
            return []
        items: list[tuple[str, dict]] = []
        for path in sorted(self._logs_dir.glob("*.md")):
            parsed = self._parse_log_file(path)
            if parsed and parsed[0] == task_id:
                items.append(parsed)
        return [item for _, item in items]

    def read_long_memory(self) -> str:
        path = self._memory_dir / LONG_MEMORY_FILENAME
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def write_long_memory(self, text: str) -> None:
        self._ensure_dirs()
        path = self._memory_dir / LONG_MEMORY_FILENAME
        path.write_text(text, encoding="utf-8")

    def append_long_memory(self, text: str) -> None:
        self._ensure_dirs()
        path = self._memory_dir / LONG_MEMORY_FILENAME
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        new_content = existing.rstrip() + ("\n\n" if existing else "") + text
        path.write_text(new_content, encoding="utf-8")

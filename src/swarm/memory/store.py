from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class MemoryStore(Protocol):
    def append(self, *, task_id: str, item: dict) -> None: ...
    def get(self, *, task_id: str) -> list[dict]: ...


@dataclass
class InMemoryStore(MemoryStore):
    _data: dict[str, list[dict]] = field(default_factory=dict)

    def append(self, *, task_id: str, item: dict) -> None:
        self._data.setdefault(task_id, []).append(item)

    def get(self, *, task_id: str) -> list[dict]:
        return list(self._data.get(task_id, []))


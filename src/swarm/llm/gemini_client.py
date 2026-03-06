from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from google import genai


class LLMClient(Protocol):
    def generate_text(self, *, prompt: str, model: str) -> str: ...


@dataclass(frozen=True)
class GeminiClient(LLMClient):
    api_key: str

    def _client(self) -> genai.Client:
        return genai.Client(api_key=self.api_key)

    def generate_text(self, *, prompt: str, model: str) -> str:
        # `google-genai` response structures vary by endpoint/version; `.text` is the stable shortcut.
        resp = self._client().models.generate_content(model=model, contents=prompt)
        text = getattr(resp, "text", None)
        if text:
            return text
        # Fallback (very defensive): stringify the response if `.text` is missing.
        return str(resp)


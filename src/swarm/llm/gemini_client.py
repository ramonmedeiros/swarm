from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from google import genai

# Reuse a single Client per api_key. Creating a new Client() per request causes
# the library to close its internal httpx client when the temporary Client is
# discarded, leading to "Cannot send a request, as the client has been closed."
_client_cache: dict[str, genai.Client] = {}


class LLMClient(Protocol):
    def generate_text(self, *, prompt: str, model: str) -> str: ...


@dataclass(frozen=True)
class GeminiClient(LLMClient):
    api_key: str

    def _client(self) -> genai.Client:
        if self.api_key not in _client_cache:
            _client_cache[self.api_key] = genai.Client(api_key=self.api_key)
        return _client_cache[self.api_key]

    def generate_text(self, *, prompt: str, model: str) -> str:
        # `google-genai` response structures vary by endpoint/version; `.text` is the stable shortcut.
        resp = self._client().models.generate_content(model=model, contents=prompt)
        text = getattr(resp, "text", None)
        if text:
            return text
        # Fallback (very defensive): stringify the response if `.text` is missing.
        return str(resp)


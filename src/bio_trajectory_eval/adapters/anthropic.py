from __future__ import annotations

import os

import httpx

from bio_trajectory_eval.adapters.base import Message, ModelAdapter, Response


class AnthropicAdapter(ModelAdapter):
    def __init__(self, model: str, timeout_seconds: int = 60):
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self._api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")

    @property
    def model_id(self) -> str:
        return self._model

    def send(self, messages: list[Message], system: str | None = None) -> Response:
        payload: dict = {
            "model": self._model,
            "max_tokens": 800,
            "messages": [{"role": item.role, "content": item.content} for item in messages],
        }
        if system:
            payload["system"] = system
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        with httpx.Client(timeout=self._timeout_seconds) as client:
            response = client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            response.raise_for_status()
            raw = response.json()
        text_parts = [part.get("text", "") for part in raw.get("content", []) if part.get("type") == "text"]
        return Response(content="\n".join(text_parts).strip(), raw=raw)

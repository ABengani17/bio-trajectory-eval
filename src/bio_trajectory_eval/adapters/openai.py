from __future__ import annotations

import os

import httpx

from bio_trajectory_eval.adapters.base import Message, ModelAdapter, Response


class OpenAIAdapter(ModelAdapter):
    def __init__(self, model: str, timeout_seconds: int = 60):
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._api_key = os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

    @property
    def model_id(self) -> str:
        return self._model

    def send(self, messages: list[Message], system: str | None = None) -> Response:
        payload_messages = []
        if system:
            payload_messages.append({"role": "system", "content": system})
        payload_messages.extend({"role": item.role, "content": item.content} for item in messages)
        payload = {
            "model": self._model,
            "messages": payload_messages,
            "max_tokens": 800,
        }
        headers = {
            "authorization": f"Bearer {self._api_key}",
            "content-type": "application/json",
        }
        with httpx.Client(timeout=self._timeout_seconds) as client:
            response = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            raw = response.json()
        content = raw["choices"][0]["message"].get("content", "")
        return Response(content=content.strip(), raw=raw)

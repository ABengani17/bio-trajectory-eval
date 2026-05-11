from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Message:
    role: str
    content: str


@dataclass(frozen=True)
class Response:
    content: str
    raw: dict | None = None


class ModelAdapter(ABC):
    @abstractmethod
    def send(self, messages: list[Message], system: str | None = None) -> Response:
        raise NotImplementedError

    @property
    @abstractmethod
    def model_id(self) -> str:
        raise NotImplementedError

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class KafkaEvent:
    topic: str
    value: dict[str, Any]
    key: str | None = None
    headers: dict[str, str] = field(default_factory=dict)


class AbstractKafkaProducer(ABC):
    @abstractmethod
    async def send(self, event: KafkaEvent) -> None:
        """Publish an event to Kafka."""

    @abstractmethod
    async def close(self) -> None:
        """Release producer resources."""


class AbstractKafkaConsumer(ABC):
    @abstractmethod
    async def start(self) -> None:
        """Initialize the consumer connection."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop the consumer cleanly."""

    @abstractmethod
    def stream(self) -> AsyncIterator[KafkaEvent]:
        """Yield events as they arrive."""

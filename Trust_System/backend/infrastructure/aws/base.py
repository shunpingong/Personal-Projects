from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SQSMessage:
    body: str
    attributes: dict[str, Any] = field(default_factory=dict)
    receipt_handle: str | None = None


class AbstractObjectStorage(ABC):
    @abstractmethod
    async def upload_bytes(
        self,
        *,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str | None = None,
    ) -> str:
        """Upload bytes and return the storage URI."""

    @abstractmethod
    async def delete_object(self, *, bucket: str, key: str) -> None:
        """Delete an object by key."""

    @abstractmethod
    async def get_object_url(self, *, bucket: str, key: str) -> str:
        """Return a public or signed object URL."""


class AbstractQueueService(ABC):
    @abstractmethod
    async def send_message(
        self,
        *,
        queue_url: str,
        body: str,
        attributes: dict[str, Any] | None = None,
    ) -> str:
        """Send a message and return its receipt handle."""

    @abstractmethod
    async def receive_messages(
        self,
        *,
        queue_url: str,
        max_messages: int = 10,
    ) -> list[SQSMessage]:
        """Receive up to max_messages messages."""

    @abstractmethod
    async def delete_message(self, *, queue_url: str, receipt_handle: str) -> None:
        """Delete a previously received message."""

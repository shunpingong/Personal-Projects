from __future__ import annotations

import logging
from uuid import uuid4

from infrastructure.aws.base import AbstractQueueService, SQSMessage


logger = logging.getLogger(__name__)


class SQSService(AbstractQueueService):
    def __init__(self) -> None:
        self._queues: dict[str, list[SQSMessage]] = {}

    async def send_message(
        self,
        *,
        queue_url: str,
        body: str,
        attributes: dict[str, object] | None = None,
    ) -> str:
        receipt_handle = str(uuid4())
        queue = self._queues.setdefault(queue_url, [])
        queue.append(
            SQSMessage(
                body=body,
                attributes=attributes or {},
                receipt_handle=receipt_handle,
            )
        )
        logger.info("SQS stub send requested for queue %s", queue_url)
        return receipt_handle

    async def receive_messages(
        self,
        *,
        queue_url: str,
        max_messages: int = 10,
    ) -> list[SQSMessage]:
        queue = self._queues.setdefault(queue_url, [])
        return queue[:max_messages]

    async def delete_message(self, *, queue_url: str, receipt_handle: str) -> None:
        queue = self._queues.setdefault(queue_url, [])
        self._queues[queue_url] = [
            message
            for message in queue
            if message.receipt_handle != receipt_handle
        ]
        logger.info("SQS stub delete requested for queue %s", queue_url)

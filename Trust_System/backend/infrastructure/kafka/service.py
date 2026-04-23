from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator

from infrastructure.kafka.base import (
    AbstractKafkaConsumer,
    AbstractKafkaProducer,
    KafkaEvent,
)


logger = logging.getLogger(__name__)


class KafkaProducerService(AbstractKafkaProducer):
    def __init__(self, brokers: list[str] | None = None) -> None:
        self.brokers = brokers or []

    async def send(self, event: KafkaEvent) -> None:
        logger.info(
            "Kafka stub publish requested",
            extra={
                "topic": event.topic,
                "key": event.key,
                "brokers": self.brokers,
            },
        )

    async def close(self) -> None:
        logger.info("Kafka producer stub closed")


class KafkaConsumerService(AbstractKafkaConsumer):
    def __init__(self, topic: str) -> None:
        self.topic = topic
        self._running = False
        self._queue: asyncio.Queue[KafkaEvent] = asyncio.Queue()

    async def start(self) -> None:
        self._running = True
        logger.info("Kafka consumer stub started for topic %s", self.topic)

    async def stop(self) -> None:
        self._running = False
        logger.info("Kafka consumer stub stopped for topic %s", self.topic)

    async def enqueue(self, event: KafkaEvent) -> None:
        await self._queue.put(event)

    async def stream(self) -> AsyncIterator[KafkaEvent]:
        while self._running:
            event = await self._queue.get()
            yield event

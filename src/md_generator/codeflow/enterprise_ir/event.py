from __future__ import annotations

from dataclasses import dataclass

from md_generator.codeflow.enterprise_ir.base import BaseEntity


@dataclass
class EventEntity(BaseEntity):
    topic: str | None
    queue: str | None
    broker: str  # Kafka, RabbitMQ, ActiveMQ, etc.
    is_publisher: bool
    is_consumer: bool
    payload_type: str | None = None
    handler_method: str | None = None

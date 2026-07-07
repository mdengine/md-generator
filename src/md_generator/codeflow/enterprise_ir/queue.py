from __future__ import annotations

from dataclasses import dataclass

from md_generator.codeflow.enterprise_ir.base import BaseEntity


@dataclass
class QueueEntity(BaseEntity):
    queue_name: str
    broker_type: str  # rabbitmq, activemq, jms, sqs, service_bus, nats
    is_durable: bool = True
    auto_delete: bool = False

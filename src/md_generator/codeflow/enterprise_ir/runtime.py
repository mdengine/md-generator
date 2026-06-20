from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from md_generator.codeflow.enterprise_ir.base import BaseEntity


@dataclass
class RuntimeEvent:
    event_name: str
    timestamp: str
    duration_ms: float
    thread_id: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuntimeEntity(BaseEntity):
    events: list[RuntimeEvent] = field(default_factory=list)
    trace_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None

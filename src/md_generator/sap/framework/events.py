from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ArtifactParsedEvent:
    artifact_id: str
    artifact_type: str
    parser_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphMergedEvent:
    graph_id: str
    fragment_id: str
    node_count: int
    edge_count: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class LineageResolvedEvent:
    run_id: str
    edges_linked: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EventBus:
    """In-process event bus stub for future async pipeline integration."""

    def __init__(self) -> None:
        self._events: list[Any] = []

    def publish(self, event: Any) -> None:
        self._events.append(event)

    @property
    def events(self) -> list[Any]:
        return list(self._events)

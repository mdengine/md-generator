from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import networkx as nx

from md_generator.sap.core.link_graph import SapLinkGraph
from md_generator.sap.core.run_config import SapRunConfig
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.parser.base import SapParseResult
from md_generator.sap.framework.events import EventBus


from md_generator.sap.models.metadata.odata import ODataMetadataDocument


@dataclass
class RunContext:
    input_paths: list[Path]
    output_dir: Path
    config: SapRunConfig
    started_at: datetime
    objects: list[SapObject] = field(default_factory=list)
    parse_results: list[SapParseResult] = field(default_factory=list)
    odata_documents: list[ODataMetadataDocument] = field(default_factory=list)
    graph: nx.MultiDiGraph | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    governance_fields: list[dict[str, Any]] = field(default_factory=list)
    link_graph: SapLinkGraph | None = None
    event_bus: EventBus | None = None

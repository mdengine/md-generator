from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Iterator

from md_generator.odata.models.domain import ODataMetadataDocument


@dataclass(slots=True)
class OdataChunk:
    chunk_id: str
    chunk_type: str
    title: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ODataServiceChunkStrategy:
    name = "odata_service"

    def iter_chunks(self, documents: list[ODataMetadataDocument]) -> Iterator[OdataChunk]:
        for doc in documents:
            yield OdataChunk(
                chunk_id=f"odata_svc:{doc.stable_id}",
                chunk_type=self.name,
                title=f"Service {doc.service_name}",
                content=json.dumps(doc.to_dict(), default=str)[:2000],
                metadata={"odata_version": doc.odata_version.value, "service": doc.service_name},
            )


class ODataEntitySetChunkStrategy:
    name = "odata_entity_set"

    def iter_chunks(self, documents: list[ODataMetadataDocument]) -> Iterator[OdataChunk]:
        for doc in documents:
            for es in doc.entity_sets:
                yield OdataChunk(
                    chunk_id=f"odata_es:{es.stable_id}",
                    chunk_type=self.name,
                    title=f"EntitySet {es.name}",
                    content=f"Entity set {es.name} type {es.entity_type} capabilities {es.capabilities.to_dict()}",
                    metadata={"stable_id": es.stable_id, "capabilities": es.capabilities.to_dict()},
                )


class ODataIndexChunkStrategy:
    name = "odata_index"

    def iter_chunks(self, documents: list[ODataMetadataDocument]) -> Iterator[OdataChunk]:
        for doc in documents:
            yield OdataChunk(
                chunk_id=f"odata_index:{doc.stable_id}",
                chunk_type=self.name,
                title=f"OData catalog {doc.service_name}",
                content=f"Service {doc.service_name} OData {doc.odata_version.value} with {len(doc.entity_sets)} entity sets",
                metadata={"service": doc.service_name, "version": doc.odata_version.value},
            )


class ODataCapabilitiesChunkStrategy:
    name = "odata_capabilities"

    def iter_chunks(self, documents: list[ODataMetadataDocument]) -> Iterator[OdataChunk]:
        for doc in documents:
            for es in doc.entity_sets:
                cap = es.capabilities.to_dict()
                yield OdataChunk(
                    chunk_id=f"odata_cap:{es.stable_id}",
                    chunk_type=self.name,
                    title=f"Capabilities {es.name}",
                    content=json.dumps(cap),
                    metadata=cap,
                )


STRATEGIES: dict[str, object] = {
    ODataServiceChunkStrategy.name: ODataServiceChunkStrategy(),
    ODataEntitySetChunkStrategy.name: ODataEntitySetChunkStrategy(),
    ODataIndexChunkStrategy.name: ODataIndexChunkStrategy(),
    ODataCapabilitiesChunkStrategy.name: ODataCapabilitiesChunkStrategy(),
}


def get_strategies(names: list[str]) -> list[object]:
    return [STRATEGIES[n] for n in names if n in STRATEGIES]

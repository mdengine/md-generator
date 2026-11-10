from __future__ import annotations

"""Canonical Knowledge Graph Data Models & Injective Composite Key Helpers.

Phase 2C Implementation: Enterprise knowledge graph schema, structured edge provenance,
canonical GraphPath representations, and strict multi-tenant boundary validation.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import urllib.parse
import re

from md_generator.semantic.model.schema import SourceLocation
from md_generator.graph.exceptions import TenantBoundaryError, GraphError

RELATIONSHIP_TYPE_REGEX = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_tenant_id(tenant_id: str, field_name: str = "tenant_id") -> str:
    """Validates that tenant_id is a non-empty, non-whitespace string."""
    if not isinstance(tenant_id, str) or not tenant_id or not tenant_id.strip():
        raise TenantBoundaryError(
            f"{field_name} must be a non-empty, non-whitespace string. Got: {tenant_id!r}"
        )
    return tenant_id.strip()


def canonical_entity_node_id(tenant_id: str, entity_id: str) -> str:
    """Authoritative entity node identity based on deterministic Entity.entity_id."""
    clean_tenant = _validate_tenant_id(tenant_id, "canonical_entity_node_id.tenant_id")
    if not isinstance(entity_id, str) or not entity_id or not entity_id.strip():
        raise ValueError(f"entity_id must be a non-empty string. Got: {entity_id!r}")
    return f"tenant:{urllib.parse.quote(clean_tenant, safe='')}:entity:{urllib.parse.quote(entity_id.strip(), safe='')}"


def canonical_typed_node_id(tenant_id: str, entity_type: str, qualified_name: str) -> str:
    """Auxiliary helper / alias identity for hierarchical type lookup."""
    clean_tenant = _validate_tenant_id(tenant_id, "canonical_typed_node_id.tenant_id")
    if not isinstance(entity_type, str) or not entity_type or not entity_type.strip():
        raise ValueError(f"entity_type must be a non-empty string. Got: {entity_type!r}")
    if not isinstance(qualified_name, str) or not qualified_name or not qualified_name.strip():
        raise ValueError(f"qualified_name must be a non-empty string. Got: {qualified_name!r}")
    return (
        f"tenant:{urllib.parse.quote(clean_tenant, safe='')}:"
        f"type:{urllib.parse.quote(entity_type.strip(), safe='')}:"
        f"name:{urllib.parse.quote(qualified_name.strip(), safe='')}"
    )


def canonical_chunk_node_id(tenant_id: str, chunk_id: str) -> str:
    """Authoritative chunk node identity."""
    clean_tenant = _validate_tenant_id(tenant_id, "canonical_chunk_node_id.tenant_id")
    if not isinstance(chunk_id, str) or not chunk_id or not chunk_id.strip():
        raise ValueError(f"chunk_id must be a non-empty string. Got: {chunk_id!r}")
    return f"tenant:{urllib.parse.quote(clean_tenant, safe='')}:chunk:{urllib.parse.quote(chunk_id.strip(), safe='')}"


def canonical_document_node_id(tenant_id: str, document_id: str) -> str:
    """Authoritative document node identity."""
    clean_tenant = _validate_tenant_id(tenant_id, "canonical_document_node_id.tenant_id")
    if not isinstance(document_id, str) or not document_id or not document_id.strip():
        raise ValueError(f"document_id must be a non-empty string. Got: {document_id!r}")
    return f"tenant:{urllib.parse.quote(clean_tenant, safe='')}:doc:{urllib.parse.quote(document_id.strip(), safe='')}"


def canonical_relation_edge_id(tenant_id: str, source_id: str, rel_type: str, target_id: str) -> str:
    """Authoritative relation edge identity."""
    clean_tenant = _validate_tenant_id(tenant_id, "canonical_relation_edge_id.tenant_id")
    if not isinstance(source_id, str) or not source_id or not source_id.strip():
        raise ValueError(f"source_id must be a non-empty string. Got: {source_id!r}")
    if not isinstance(target_id, str) or not target_id or not target_id.strip():
        raise ValueError(f"target_id must be a non-empty string. Got: {target_id!r}")
    if not isinstance(rel_type, str) or not RELATIONSHIP_TYPE_REGEX.fullmatch(rel_type):
        raise ValueError(
            f"rel_type must match regex '^[A-Za-z_][A-Za-z0-9_]*$'. Got: {rel_type!r}"
        )
    return (
        f"tenant:{urllib.parse.quote(clean_tenant, safe='')}:rel:"
        f"{urllib.parse.quote(source_id.strip(), safe='')}->"
        f"{urllib.parse.quote(rel_type, safe='')}->"
        f"{urllib.parse.quote(target_id.strip(), safe='')}"
    )


@dataclass(frozen=True)
class EdgeProvenance:
    """Tracks document and chunk provenance for a graph relationship edge."""
    document_id: str
    chunk_id: Optional[str] = None
    confidence: float = 1.0
    source_location: Optional[SourceLocation] = None

    def __post_init__(self) -> None:
        if not isinstance(self.document_id, str) or not self.document_id.strip():
            raise ValueError("EdgeProvenance.document_id must be a non-empty string.")
        if isinstance(self.confidence, bool) or not isinstance(self.confidence, (int, float)) or not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"EdgeProvenance.confidence must be a float in [0.0, 1.0]. Got: {self.confidence!r}")

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "confidence": self.confidence,
        }
        if self.source_location is not None:
            d["source_location"] = self.source_location.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EdgeProvenance:
        if not isinstance(data, dict):
            raise ValueError("Input to from_dict must be a dictionary.")
        loc = SourceLocation.from_dict(data["source_location"]) if data.get("source_location") else None
        return cls(
            document_id=data["document_id"],
            chunk_id=data.get("chunk_id"),
            confidence=float(data.get("confidence", 1.0)),
            source_location=loc,
        )


@dataclass(frozen=True)
class GraphPath:
    """Canonical representation of a graph traversal path from a seed node."""
    seed_chunk_id: str
    target_node_id: str
    node_ids: List[str]
    edge_ids: List[str]
    depth: int
    score: float

    def __post_init__(self) -> None:
        if not isinstance(self.seed_chunk_id, str) or not self.seed_chunk_id.strip():
            raise ValueError("GraphPath.seed_chunk_id must be a non-empty string.")
        if not isinstance(self.target_node_id, str) or not self.target_node_id.strip():
            raise ValueError("GraphPath.target_node_id must be a non-empty string.")
        if isinstance(self.depth, bool) or not isinstance(self.depth, int) or self.depth < 0:
            raise ValueError(f"GraphPath.depth must be an integer >= 0. Got: {self.depth!r}")
        if isinstance(self.score, bool) or not isinstance(self.score, (int, float)) or not (0.0 <= self.score <= 1.0):
            raise ValueError(f"GraphPath.score must be a float in [0.0, 1.0]. Got: {self.score!r}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed_chunk_id": self.seed_chunk_id,
            "target_node_id": self.target_node_id,
            "node_ids": list(self.node_ids),
            "edge_ids": list(self.edge_ids),
            "depth": self.depth,
            "score": self.score,
        }


@dataclass
class EntityNode:
    """Canonical Knowledge Graph entity node."""
    node_id: str
    tenant_id: str
    entity_id: str
    entity_type: str
    name: str
    qualified_name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    document_ids: List[str] = field(default_factory=list)
    chunk_ids: List[str] = field(default_factory=list)
    source_location: Optional[SourceLocation] = None

    def __post_init__(self) -> None:
        self.tenant_id = _validate_tenant_id(self.tenant_id, "EntityNode.tenant_id")
        if not self.node_id or not isinstance(self.node_id, str) or not self.node_id.strip():
            raise ValueError("EntityNode.node_id must be a non-empty string.")
        if not self.entity_id or not isinstance(self.entity_id, str) or not self.entity_id.strip():
            raise ValueError("EntityNode.entity_id must be a non-empty string.")
        if not self.entity_type or not isinstance(self.entity_type, str) or not self.entity_type.strip():
            raise ValueError("EntityNode.entity_type must be a non-empty string.")
        if not self.name or not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("EntityNode.name must be a non-empty string.")
        if not self.qualified_name or not isinstance(self.qualified_name, str) or not self.qualified_name.strip():
            raise ValueError("EntityNode.qualified_name must be a non-empty string.")

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "node_id": self.node_id,
            "tenant_id": self.tenant_id,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "name": self.name,
            "qualified_name": self.qualified_name,
            "properties": dict(self.properties),
            "document_ids": list(self.document_ids),
            "chunk_ids": list(self.chunk_ids),
        }
        if self.source_location is not None:
            d["source_location"] = self.source_location.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EntityNode:
        if not isinstance(data, dict):
            raise ValueError("Input to from_dict must be a dictionary.")
        loc = SourceLocation.from_dict(data["source_location"]) if data.get("source_location") else None
        return cls(
            node_id=data["node_id"],
            tenant_id=data["tenant_id"],
            entity_id=data["entity_id"],
            entity_type=data["entity_type"],
            name=data["name"],
            qualified_name=data["qualified_name"],
            properties=dict(data.get("properties", {})),
            document_ids=list(data.get("document_ids", [])),
            chunk_ids=list(data.get("chunk_ids", [])),
            source_location=loc,
        )


@dataclass
class RelationEdge:
    """Canonical Knowledge Graph relationship edge with multi-document provenance."""
    edge_id: str
    tenant_id: str
    source_id: str
    target_id: str
    relationship_type: str
    weight: float = 1.0
    document_ids: List[str] = field(default_factory=list)
    chunk_ids: List[str] = field(default_factory=list)
    provenance: List[EdgeProvenance] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.tenant_id = _validate_tenant_id(self.tenant_id, "RelationEdge.tenant_id")
        if not self.edge_id or not isinstance(self.edge_id, str) or not self.edge_id.strip():
            raise ValueError("RelationEdge.edge_id must be a non-empty string.")
        if not self.source_id or not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("RelationEdge.source_id must be a non-empty string.")
        if not self.target_id or not isinstance(self.target_id, str) or not self.target_id.strip():
            raise ValueError("RelationEdge.target_id must be a non-empty string.")
        if not self.relationship_type or not isinstance(self.relationship_type, str):
            raise ValueError("RelationEdge.relationship_type must be a non-empty string.")
        if not RELATIONSHIP_TYPE_REGEX.fullmatch(self.relationship_type):
            raise ValueError(
                f"RelationEdge.relationship_type must match regex '^[A-Za-z_][A-Za-z0-9_]*$'. Got: {self.relationship_type!r}"
            )
        if isinstance(self.weight, bool) or not isinstance(self.weight, (int, float)) or not (0.0 <= self.weight <= 1.0):
            raise ValueError(f"RelationEdge.weight must be a float in [0.0, 1.0]. Got: {self.weight!r}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "tenant_id": self.tenant_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type,
            "weight": self.weight,
            "document_ids": list(self.document_ids),
            "chunk_ids": list(self.chunk_ids),
            "provenance": [p.to_dict() for p in self.provenance],
            "properties": dict(self.properties),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RelationEdge:
        if not isinstance(data, dict):
            raise ValueError("Input to from_dict must be a dictionary.")
        provs = [EdgeProvenance.from_dict(p) for p in data.get("provenance", [])]
        return cls(
            edge_id=data["edge_id"],
            tenant_id=data["tenant_id"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            relationship_type=data["relationship_type"],
            weight=float(data.get("weight", 1.0)),
            document_ids=list(data.get("document_ids", [])),
            chunk_ids=list(data.get("chunk_ids", [])),
            provenance=provs,
            properties=dict(data.get("properties", {})),
        )


@dataclass
class KnowledgeGraph:
    """Unified multi-tenant knowledge graph container."""
    tenant_id: str
    nodes: Dict[str, EntityNode] = field(default_factory=dict)
    edges: Dict[str, RelationEdge] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        clean_tenant = _validate_tenant_id(self.tenant_id, "KnowledgeGraph.tenant_id")
        self.tenant_id = clean_tenant

        for node_id, node in self.nodes.items():
            if node.tenant_id != self.tenant_id:
                raise TenantBoundaryError(
                    f"EntityNode '{node_id}' has tenant_id '{node.tenant_id}' conflicting with graph tenant_id '{self.tenant_id}'."
                )

        for edge_id, edge in self.edges.items():
            if edge.tenant_id != self.tenant_id:
                raise TenantBoundaryError(
                    f"RelationEdge '{edge_id}' has tenant_id '{edge.tenant_id}' conflicting with graph tenant_id '{self.tenant_id}'."
                )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": {k: v.to_dict() for k, v in self.edges.items()},
            "metadata": dict(self.metadata),
        }

    def to_json_ld(self, include_tenant: bool = False) -> Dict[str, Any]:
        """Serializes to W3C JSON-LD format with canonical ontology context."""
        from md_generator.graph.serialization import to_json_ld
        return to_json_ld(self, include_tenant=include_tenant)

    def to_cytoscape(self) -> Dict[str, Any]:
        """Serializes to Cytoscape elements schema for interactive graph visualization."""
        from md_generator.graph.serialization import to_cytoscape
        return to_cytoscape(self)

    def to_cypher_statements(self) -> List[str]:
        """Generates deterministic Cypher MERGE statements representing the graph."""
        from md_generator.graph.serialization import to_cypher_statements
        return to_cypher_statements(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> KnowledgeGraph:
        if not isinstance(data, dict):
            raise ValueError("Input to from_dict must be a dictionary.")
        nodes = {k: EntityNode.from_dict(v) for k, v in data.get("nodes", {}).items()}
        edges = {k: RelationEdge.from_dict(v) for k, v in data.get("edges", {}).items()}
        return cls(
            tenant_id=data["tenant_id"],
            nodes=nodes,
            edges=edges,
            metadata=dict(data.get("metadata", {})),
        )


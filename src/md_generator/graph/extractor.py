from __future__ import annotations

"""Knowledge Graph Extractor for SemanticDocument and SemanticChunk models.

Phase 2C Implementation: Ingests SemanticDocument and List[SemanticChunk] without mutation,
enforcing explicit tenant binding, Option A deterministic deduplication, and
referential integrity between entities, chunks, and documents.
"""

from typing import List, Dict, Any, Optional
import re

from md_generator.semantic.model.schema import SemanticDocument, SemanticChunk, Entity, Relationship
from md_generator.graph.model import (
    EntityNode,
    RelationEdge,
    KnowledgeGraph,
    EdgeProvenance,
    canonical_entity_node_id,
    canonical_chunk_node_id,
    canonical_document_node_id,
    canonical_relation_edge_id,
    _validate_tenant_id,
    RELATIONSHIP_TYPE_REGEX,
)
from md_generator.graph.exceptions import TenantBoundaryError, GraphError


def _sanitize_relationship_type(rel_type: str) -> str:
    """Sanitizes a relationship type string to strictly match '^[A-Za-z_][A-Za-z0-9_]*$'."""
    if not rel_type or not isinstance(rel_type, str):
        return "RELATED_TO"
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", rel_type.strip()).upper()
    if not cleaned:
        return "RELATED_TO"
    if cleaned[0].isdigit():
        cleaned = f"REL_{cleaned}"
    if not RELATIONSHIP_TYPE_REGEX.fullmatch(cleaned):
        return "RELATED_TO"
    return cleaned


def extract(
    semantic_document: SemanticDocument,
    chunks: List[SemanticChunk],
    tenant_id: str,
) -> KnowledgeGraph:
    """Extracts a unified KnowledgeGraph from a SemanticDocument and its SemanticChunks.
    
    Invariants:
    1. tenant_id is mandatory, non-empty, and validated. No inference from metadata.system.
    2. Zero in-place mutation of semantic_document or chunks.
    3. Option A deduplication: Unifies document-level and chunk-level entities/relationships.
    4. Deterministic property conflict precedence: chunk > document for scalar keys.
    5. Structural nodes: Document and Chunk nodes created with CONTAINS_CHUNK and CONTAINS_ENTITY edges.
    """
    clean_tenant = _validate_tenant_id(tenant_id, "extract.tenant_id")

    if not isinstance(semantic_document, SemanticDocument):
        raise GraphError("semantic_document must be an instance of SemanticDocument.")
    if not isinstance(chunks, list):
        raise GraphError("chunks must be a list of SemanticChunk instances.")

    doc_id = semantic_document.document_id
    if not doc_id:
        raise GraphError("semantic_document must have a valid document_id.")

    extracted_nodes: Dict[str, EntityNode] = {}
    extracted_edges: Dict[str, RelationEdge] = {}

    # 1. Structural Document Node
    doc_node_id = canonical_document_node_id(clean_tenant, doc_id)
    doc_node = EntityNode(
        node_id=doc_node_id,
        tenant_id=clean_tenant,
        entity_id=doc_id,
        entity_type="document",
        name=semantic_document.document_type or "document",
        qualified_name=f"document.{doc_id}",
        properties={
            "document_type": semantic_document.document_type,
            "schema_version": semantic_document.schema_version,
            "sanitized_length": len(semantic_document.sanitized_content or ""),
        },
        document_ids=[doc_id],
        chunk_ids=[c.chunk_id for c in chunks if c.chunk_id],
        source_location=None,
    )
    extracted_nodes[doc_node_id] = doc_node

    # 2. Structural Chunk Nodes & CONTAINS_CHUNK Edges
    for chunk in chunks:
        cid = chunk.chunk_id
        if not cid:
            continue
        chunk_node_id = canonical_chunk_node_id(clean_tenant, cid)
        loc = chunk.lineage.location if chunk.lineage else None
        chunk_node = EntityNode(
            node_id=chunk_node_id,
            tenant_id=clean_tenant,
            entity_id=cid,
            entity_type="chunk",
            name=f"chunk_{cid[:8]}",
            qualified_name=f"chunk.{cid}",
            properties={
                "sanitized_length": len(chunk.sanitized_content or ""),
            },
            document_ids=[doc_id],
            chunk_ids=[cid],
            source_location=loc,
        )
        extracted_nodes[chunk_node_id] = chunk_node

        # Edge: (Document)-[:CONTAINS_CHUNK]->(Chunk)
        contains_chunk_edge_id = canonical_relation_edge_id(
            clean_tenant, doc_node_id, "CONTAINS_CHUNK", chunk_node_id
        )
        extracted_edges[contains_chunk_edge_id] = RelationEdge(
            edge_id=contains_chunk_edge_id,
            tenant_id=clean_tenant,
            source_id=doc_node_id,
            target_id=chunk_node_id,
            relationship_type="CONTAINS_CHUNK",
            weight=1.0,
            document_ids=[doc_id],
            chunk_ids=[cid],
            provenance=[EdgeProvenance(document_id=doc_id, chunk_id=cid, confidence=1.0, source_location=loc)],
            properties={"structural": True},
        )

    # Helper for merging entity properties deterministically
    def _merge_properties(existing_props: Dict[str, Any], new_props: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(existing_props)
        for k, v in new_props.items():
            if k in merged:
                exist_val = merged[k]
                if isinstance(exist_val, (list, set)) and isinstance(v, (list, set)):
                    merged[k] = sorted(list(set(exist_val).union(set(v))))
                else:
                    # Scalar conflict: new value (chunk) overrides existing (document)
                    merged[k] = v
            else:
                merged[k] = v
        return merged

    # 3. Document-Level Entities (Base)
    for ent in semantic_document.entities:
        if not ent.entity_id:
            continue
        ent_node_id = canonical_entity_node_id(clean_tenant, ent.entity_id)
        extracted_nodes[ent_node_id] = EntityNode(
            node_id=ent_node_id,
            tenant_id=clean_tenant,
            entity_id=ent.entity_id,
            entity_type=ent.entity_type,
            name=ent.name,
            qualified_name=ent.qualified_name,
            properties=dict(ent.metadata),
            document_ids=[doc_id],
            chunk_ids=[],
            source_location=ent.location,
        )

    # 4. Chunk-Level Entities (Enrichment) & CONTAINS_ENTITY Edges
    for chunk in chunks:
        cid = chunk.chunk_id
        chunk_node_id = canonical_chunk_node_id(clean_tenant, cid) if cid else None

        for ent in chunk.entities:
            if not ent.entity_id:
                continue
            ent_node_id = canonical_entity_node_id(clean_tenant, ent.entity_id)

            if ent_node_id in extracted_nodes:
                node = extracted_nodes[ent_node_id]
                if doc_id not in node.document_ids:
                    node.document_ids.append(doc_id)
                if cid and cid not in node.chunk_ids:
                    node.chunk_ids.append(cid)
                node.properties = _merge_properties(node.properties, ent.metadata)
                if ent.location and not node.source_location:
                    node.source_location = ent.location
            else:
                extracted_nodes[ent_node_id] = EntityNode(
                    node_id=ent_node_id,
                    tenant_id=clean_tenant,
                    entity_id=ent.entity_id,
                    entity_type=ent.entity_type,
                    name=ent.name,
                    qualified_name=ent.qualified_name,
                    properties=dict(ent.metadata),
                    document_ids=[doc_id],
                    chunk_ids=[cid] if cid else [],
                    source_location=ent.location,
                )

            # Edge: (Chunk)-[:CONTAINS_ENTITY]->(Entity)
            if chunk_node_id:
                contains_ent_edge_id = canonical_relation_edge_id(
                    clean_tenant, chunk_node_id, "CONTAINS_ENTITY", ent_node_id
                )
                if contains_ent_edge_id in extracted_edges:
                    edge = extracted_edges[contains_ent_edge_id]
                    if doc_id not in edge.document_ids:
                        edge.document_ids.append(doc_id)
                    if cid and cid not in edge.chunk_ids:
                        edge.chunk_ids.append(cid)
                else:
                    extracted_edges[contains_ent_edge_id] = RelationEdge(
                        edge_id=contains_ent_edge_id,
                        tenant_id=clean_tenant,
                        source_id=chunk_node_id,
                        target_id=ent_node_id,
                        relationship_type="CONTAINS_ENTITY",
                        weight=1.0,
                        document_ids=[doc_id],
                        chunk_ids=[cid] if cid else [],
                        provenance=[EdgeProvenance(document_id=doc_id, chunk_id=cid, confidence=1.0, source_location=ent.location)],
                        properties={"structural": True},
                    )

    # 5. Document-Level Relationships
    for rel in semantic_document.relationships:
        if not rel.source_entity_id or not rel.target_entity_id:
            continue
        src_id = canonical_entity_node_id(clean_tenant, rel.source_entity_id)
        tgt_id = canonical_entity_node_id(clean_tenant, rel.target_entity_id)
        rtype = _sanitize_relationship_type(rel.relationship_type)
        edge_id = canonical_relation_edge_id(clean_tenant, src_id, rtype, tgt_id)

        conf = float(rel.confidence) if isinstance(rel.confidence, (int, float)) else 1.0
        prov = EdgeProvenance(document_id=doc_id, chunk_id=None, confidence=conf)

        if edge_id in extracted_edges:
            edge = extracted_edges[edge_id]
            if doc_id not in edge.document_ids:
                edge.document_ids.append(doc_id)
            edge.weight = max(edge.weight, conf)
            edge.provenance.append(prov)
            edge.properties = _merge_properties(edge.properties, rel.provenance)
        else:
            extracted_edges[edge_id] = RelationEdge(
                edge_id=edge_id,
                tenant_id=clean_tenant,
                source_id=src_id,
                target_id=tgt_id,
                relationship_type=rtype,
                weight=conf,
                document_ids=[doc_id],
                chunk_ids=[],
                provenance=[prov],
                properties=dict(rel.provenance),
            )

    # 6. Chunk-Level Relationships
    for chunk in chunks:
        cid = chunk.chunk_id
        for rel in chunk.relationships:
            if not rel.source_entity_id or not rel.target_entity_id:
                continue
            src_id = canonical_entity_node_id(clean_tenant, rel.source_entity_id)
            tgt_id = canonical_entity_node_id(clean_tenant, rel.target_entity_id)
            rtype = _sanitize_relationship_type(rel.relationship_type)
            edge_id = canonical_relation_edge_id(clean_tenant, src_id, rtype, tgt_id)

            conf = float(rel.confidence) if isinstance(rel.confidence, (int, float)) else 1.0
            prov = EdgeProvenance(document_id=doc_id, chunk_id=cid, confidence=conf)

            if edge_id in extracted_edges:
                edge = extracted_edges[edge_id]
                if doc_id not in edge.document_ids:
                    edge.document_ids.append(doc_id)
                if cid and cid not in edge.chunk_ids:
                    edge.chunk_ids.append(cid)
                edge.weight = max(edge.weight, conf)
                edge.provenance.append(prov)
                edge.properties = _merge_properties(edge.properties, rel.provenance)
            else:
                extracted_edges[edge_id] = RelationEdge(
                    edge_id=edge_id,
                    tenant_id=clean_tenant,
                    source_id=src_id,
                    target_id=tgt_id,
                    relationship_type=rtype,
                    weight=conf,
                    document_ids=[doc_id],
                    chunk_ids=[cid] if cid else [],
                    provenance=[prov],
                    properties=dict(rel.provenance),
                )

    kg = KnowledgeGraph(
        tenant_id=clean_tenant,
        nodes=extracted_nodes,
        edges=extracted_edges,
        metadata={
            "document_id": doc_id,
            "chunk_count": len(chunks),
            "node_count": len(extracted_nodes),
            "edge_count": len(extracted_edges),
        },
    )
    return kg

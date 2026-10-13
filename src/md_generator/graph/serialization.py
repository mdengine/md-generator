from __future__ import annotations

"""Knowledge Graph Serialization: JSON-LD, Cytoscape, and Cypher Export.

Phase 2C Implementation: Export knowledge graphs to W3C JSON-LD with canonical ontology context,
Cytoscape elements JSON schema for interactive graph visualization,
and deterministic parameterized Cypher statements.
"""

import json
from typing import Any, Dict, List, Optional

from md_generator.graph.model import KnowledgeGraph, RELATIONSHIP_TYPE_REGEX

JSON_LD_CONTEXT: Dict[str, Any] = {
    "kg": "https://mdengine.dev/ontology#",
    "Entity": "kg:Entity",
    "Relation": "kg:Relation",
    "Chunk": "kg:Chunk",
    "nodeId": "@id",
    "entityType": "@type",
    "name": "kg:name",
    "qualifiedName": "kg:qualifiedName",
    "properties": "kg:properties",
    "chunkIds": "kg:chunkIds",
    "relationshipType": "kg:relationshipType",
    "source": "kg:source",
    "target": "kg:target",
    "weight": "kg:weight",
}


def to_dict(graph: KnowledgeGraph) -> Dict[str, Any]:
    """Serializes KnowledgeGraph to canonical dictionary format."""
    return graph.to_dict()


def _strip_tenant_prefix(identifier: str, tenant_id: str) -> str:
    """Strips tenant:<tenant_id>: prefix from canonical identifier for external privacy."""
    prefix = f"tenant:{tenant_id}:"
    if identifier.startswith(prefix):
        return identifier[len(prefix):]
    return identifier


def to_json_ld(graph: KnowledgeGraph, include_tenant: bool = False) -> Dict[str, Any]:
    """Serializes KnowledgeGraph to W3C JSON-LD format with canonical ontology context.
    
    Security note: include_tenant is False by default to prevent leaking internal
    tenant identifiers in external or shared graph exports. When include_tenant=False,
    all tenantId fields are omitted AND tenant prefixes are stripped from canonical IDs
    (e.g., 'tenant:t1:entity:cls_order' becomes 'entity:cls_order').
    """
    nodes_ld = []
    # Sort nodes deterministically by node_id
    for node_id in sorted(graph.nodes.keys()):
        node = graph.nodes[node_id]
        clean_node_id = node.node_id if include_tenant else _strip_tenant_prefix(node.node_id, node.tenant_id)
        item: Dict[str, Any] = {
            "@id": clean_node_id,
            "@type": f"kg:{node.entity_type.capitalize()}",
            "entityType": node.entity_type,
            "name": node.name,
            "qualifiedName": node.qualified_name,
            "properties": dict(node.properties),
            "chunkIds": list(node.chunk_ids),
        }
        if include_tenant:
            item["tenantId"] = node.tenant_id
        nodes_ld.append(item)

    edges_ld = []
    # Sort edges deterministically by edge_id
    for edge_id in sorted(graph.edges.keys()):
        edge = graph.edges[edge_id]
        clean_edge_id = edge.edge_id if include_tenant else _strip_tenant_prefix(edge.edge_id, edge.tenant_id)
        clean_src_id = edge.source_id if include_tenant else _strip_tenant_prefix(edge.source_id, edge.tenant_id)
        clean_tgt_id = edge.target_id if include_tenant else _strip_tenant_prefix(edge.target_id, edge.tenant_id)
        item = {
            "@id": clean_edge_id,
            "@type": "kg:Relation",
            "relationshipType": edge.relationship_type,
            "source": clean_src_id,
            "target": clean_tgt_id,
            "weight": edge.weight,
            "properties": dict(edge.properties),
        }
        if include_tenant:
            item["tenantId"] = edge.tenant_id
        edges_ld.append(item)

    result: Dict[str, Any] = {
        "@context": dict(JSON_LD_CONTEXT),
        "@graph": {
            "nodes": nodes_ld,
            "edges": edges_ld,
        },
    }
    if include_tenant:
        result["tenantId"] = graph.tenant_id

    return result


def to_cytoscape(graph: KnowledgeGraph) -> Dict[str, Any]:
    """Serializes KnowledgeGraph to Cytoscape JSON elements schema for graph visualization."""
    cy_nodes = []
    for node_id in sorted(graph.nodes.keys()):
        node = graph.nodes[node_id]
        cy_nodes.append({
            "data": {
                "id": node.node_id,
                "label": node.name,
                "type": node.entity_type,
                "qualified_name": node.qualified_name,
                "properties": dict(node.properties),
                "chunk_ids": list(node.chunk_ids),
            }
        })

    cy_edges = []
    for edge_id in sorted(graph.edges.keys()):
        edge = graph.edges[edge_id]
        cy_edges.append({
            "data": {
                "id": edge.edge_id,
                "source": edge.source_id,
                "target": edge.target_id,
                "label": edge.relationship_type,
                "weight": edge.weight,
                "properties": dict(edge.properties),
            }
        })

    return {
        "elements": {
            "nodes": cy_nodes,
            "edges": cy_edges,
        }
    }


def to_cypher_statements(graph: KnowledgeGraph) -> List[str]:
    """Generates deterministic Cypher MERGE statements representing the graph."""
    statements: List[str] = []

    # Sort nodes deterministically
    for node_id in sorted(graph.nodes.keys()):
        node = graph.nodes[node_id]
        props_json = json.dumps(node.properties, sort_keys=True)
        doc_ids_json = json.dumps(node.document_ids, sort_keys=True)
        chunk_ids_json = json.dumps(node.chunk_ids, sort_keys=True)

        stmt = (
            f"MERGE (n:EntityNode {{tenant_id: '{node.tenant_id}', node_id: '{node.node_id}'}}) "
            f"SET n.entity_id = '{node.entity_id}', "
            f"    n.entity_type = '{node.entity_type}', "
            f"    n.name = '{node.name}', "
            f"    n.qualified_name = '{node.qualified_name}', "
            f"    n.properties = '{props_json}', "
            f"    n.document_ids = {doc_ids_json}, "
            f"    n.chunk_ids = {chunk_ids_json};"
        )
        statements.append(stmt)

    # Sort edges deterministically
    for edge_id in sorted(graph.edges.keys()):
        edge = graph.edges[edge_id]
        if not RELATIONSHIP_TYPE_REGEX.fullmatch(edge.relationship_type):
            rel_type = "RELATED_TO"
        else:
            rel_type = edge.relationship_type

        props_json = json.dumps(edge.properties, sort_keys=True)
        doc_ids_json = json.dumps(edge.document_ids, sort_keys=True)
        chunk_ids_json = json.dumps(edge.chunk_ids, sort_keys=True)

        stmt = (
            f"MATCH (s:EntityNode {{tenant_id: '{edge.tenant_id}', node_id: '{edge.source_id}'}}) "
            f"MATCH (t:EntityNode {{tenant_id: '{edge.tenant_id}', node_id: '{edge.target_id}'}}) "
            f"MERGE (s)-[r:`{rel_type}` {{tenant_id: '{edge.tenant_id}', edge_id: '{edge.edge_id}'}}]->(t) "
            f"SET r.weight = {edge.weight:.4f}, "
            f"    r.document_ids = {doc_ids_json}, "
            f"    r.chunk_ids = {chunk_ids_json}, "
            f"    r.properties = '{props_json}';"
        )
        statements.append(stmt)

    return statements

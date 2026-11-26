"""Enterprise Knowledge Graph, Neo4j, and Hybrid GraphRAG infrastructure layer."""

from md_generator.graph.exceptions import (
    GraphError,
    Neo4jDependencyError,
    GraphStoreError,
    GraphQueryError,
    TenantBoundaryError,
)
from md_generator.graph.model import (
    EntityNode,
    RelationEdge,
    KnowledgeGraph,
    EdgeProvenance,
    GraphPath,
    GraphTombstone,
    canonical_entity_node_id,
    canonical_typed_node_id,
    canonical_chunk_node_id,
    canonical_document_node_id,
    canonical_page_node_id,
    canonical_slide_node_id,
    canonical_section_node_id,
    canonical_table_node_id,
    canonical_image_node_id,
    canonical_tombstone_node_id,
    canonical_relation_edge_id,
)
from md_generator.graph.protocol import GraphStore
from md_generator.graph.extractor import extract
from md_generator.graph.entity_extractor import BaseEntityExtractor, RuleBasedEntityExtractor
from md_generator.graph.tombstone import TombstoneManager
from md_generator.graph.reconciler import (
    GraphReconciler,
    ReconciliationDiff,
    ReconciliationResult,
    compute_document_content_hash,
)
from md_generator.graph.stores.in_memory import InMemoryGraphStore
from md_generator.graph.stores.neo4j import Neo4jGraphStore, GraphStoreFactory
from md_generator.graph.hybrid.retriever import HybridGraphRAGRetriever, ScoredHybridResult
from md_generator.graph.hybrid.context import GraphContextAdapter
from md_generator.graph.serialization import (
    to_dict,
    to_json_ld,
    to_cytoscape,
    to_cypher_statements,
)

__all__: list[str] = [
    "GraphError",
    "Neo4jDependencyError",
    "GraphStoreError",
    "GraphQueryError",
    "TenantBoundaryError",
    "EntityNode",
    "RelationEdge",
    "KnowledgeGraph",
    "EdgeProvenance",
    "GraphPath",
    "GraphTombstone",
    "canonical_entity_node_id",
    "canonical_typed_node_id",
    "canonical_chunk_node_id",
    "canonical_document_node_id",
    "canonical_page_node_id",
    "canonical_slide_node_id",
    "canonical_section_node_id",
    "canonical_table_node_id",
    "canonical_image_node_id",
    "canonical_tombstone_node_id",
    "canonical_relation_edge_id",
    "GraphStore",
    "extract",
    "BaseEntityExtractor",
    "RuleBasedEntityExtractor",
    "TombstoneManager",
    "GraphReconciler",
    "ReconciliationDiff",
    "ReconciliationResult",
    "compute_document_content_hash",
    "InMemoryGraphStore",
    "Neo4jGraphStore",
    "GraphStoreFactory",
    "HybridGraphRAGRetriever",
    "ScoredHybridResult",
    "GraphContextAdapter",
    "to_dict",
    "to_json_ld",
    "to_cytoscape",
    "to_cypher_statements",
]

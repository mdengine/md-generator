import pytest

from md_generator.graph.exceptions import TenantBoundaryError
from md_generator.graph.model import (
    EntityNode,
    RelationEdge,
    KnowledgeGraph,
    EdgeProvenance,
    GraphPath,
    canonical_entity_node_id,
    canonical_typed_node_id,
    canonical_chunk_node_id,
    canonical_document_node_id,
    canonical_relation_edge_id,
)
from md_generator.semantic.model.schema import SourceLocation


def test_edge_provenance_validation():
    prov = EdgeProvenance(document_id="doc-1", chunk_id="chunk-1", confidence=0.85)
    assert prov.document_id == "doc-1"
    assert prov.chunk_id == "chunk-1"
    assert prov.confidence == 0.85

    # Dict roundtrip
    d = prov.to_dict()
    restored = EdgeProvenance.from_dict(d)
    assert restored.document_id == prov.document_id
    assert restored.confidence == prov.confidence

    # Invalid empty doc
    with pytest.raises(ValueError):
        EdgeProvenance(document_id="")

    # Invalid confidence bounds
    with pytest.raises(ValueError):
        EdgeProvenance(document_id="doc-1", confidence=1.5)
    with pytest.raises(ValueError):
        EdgeProvenance(document_id="doc-1", confidence=-0.1)
    with pytest.raises(ValueError):
        EdgeProvenance(document_id="doc-1", confidence=True)  # type: ignore


def test_graph_path_validation():
    path = GraphPath(
        seed_chunk_id="chunk-1",
        target_node_id="node-2",
        node_ids=["node-1", "node-2"],
        edge_ids=["edge-1"],
        depth=1,
        score=0.5,
    )
    assert path.seed_chunk_id == "chunk-1"
    assert path.score == 0.5

    d = path.to_dict()
    assert d["depth"] == 1

    # Invalid depth or score
    with pytest.raises(ValueError):
        GraphPath(seed_chunk_id="c", target_node_id="t", node_ids=[], edge_ids=[], depth=-1, score=0.5)
    with pytest.raises(ValueError):
        GraphPath(seed_chunk_id="c", target_node_id="t", node_ids=[], edge_ids=[], depth=1, score=1.2)
    with pytest.raises(ValueError):
        GraphPath(seed_chunk_id="c", target_node_id="t", node_ids=[], edge_ids=[], depth=1, score=False)  # type: ignore


def test_entity_node_validation_and_serialization():
    loc = SourceLocation(location_type="code", path="src/main.py", line_start=10, line_end=20)
    node = EntityNode(
        node_id="n-1",
        tenant_id="tenant-alpha",
        entity_id="func_process",
        entity_type="function",
        name="process",
        qualified_name="module.process",
        properties={"async": True},
        document_ids=["doc-1"],
        chunk_ids=["chunk-1"],
        source_location=loc,
    )

    d = node.to_dict()
    restored = EntityNode.from_dict(d)
    assert restored.node_id == node.node_id
    assert restored.tenant_id == node.tenant_id
    assert restored.entity_id == node.entity_id
    assert restored.properties == {"async": True}
    assert restored.source_location is not None
    assert restored.source_location.line_start == 10

    # Tenant validation
    with pytest.raises(TenantBoundaryError):
        EntityNode(
            node_id="n", tenant_id="", entity_id="e", entity_type="t", name="n", qualified_name="q"
        )


def test_relation_edge_validation_and_serialization():
    prov = EdgeProvenance(document_id="doc-1", chunk_id="chunk-1", confidence=0.9)
    edge = RelationEdge(
        edge_id="e-1",
        tenant_id="tenant-alpha",
        source_id="src-1",
        target_id="tgt-1",
        relationship_type="CALLS",
        weight=0.9,
        document_ids=["doc-1"],
        chunk_ids=["chunk-1"],
        provenance=[prov],
        properties={"call_type": "async"},
    )

    d = edge.to_dict()
    restored = RelationEdge.from_dict(d)
    assert restored.edge_id == edge.edge_id
    assert restored.relationship_type == "CALLS"
    assert restored.weight == 0.9
    assert len(restored.provenance) == 1
    assert restored.provenance[0].confidence == 0.9

    # Invalid regex relationship type
    with pytest.raises(ValueError):
        RelationEdge(
            edge_id="e", tenant_id="t", source_id="s", target_id="tg", relationship_type="CALLS-METHOD"
        )
    with pytest.raises(ValueError):
        RelationEdge(
            edge_id="e", tenant_id="t", source_id="s", target_id="tg", relationship_type="123INVALID"
        )


def test_knowledge_graph_multi_tenant_consistency():
    node1 = EntityNode(
        node_id="n-1", tenant_id="tenant-alpha", entity_id="e1", entity_type="class", name="A", qualified_name="a.A"
    )
    edge1 = RelationEdge(
        edge_id="e-1", tenant_id="tenant-alpha", source_id="n-1", target_id="n-2", relationship_type="EXTENDS"
    )

    kg = KnowledgeGraph(
        tenant_id="tenant-alpha",
        nodes={"n-1": node1},
        edges={"e-1": edge1},
        metadata={"version": 1},
    )
    assert kg.tenant_id == "tenant-alpha"
    assert len(kg.nodes) == 1

    d = kg.to_dict()
    restored = KnowledgeGraph.from_dict(d)
    assert restored.tenant_id == kg.tenant_id
    assert "n-1" in restored.nodes

    # Conflict: node tenant mismatch
    node_bad = EntityNode(
        node_id="n-bad", tenant_id="tenant-beta", entity_id="e2", entity_type="class", name="B", qualified_name="b.B"
    )
    with pytest.raises(TenantBoundaryError):
        KnowledgeGraph(
            tenant_id="tenant-alpha",
            nodes={"n-bad": node_bad},
        )


def test_canonical_typed_node_id():
    tid = canonical_typed_node_id("tenant-1", "class", "module.sub.MyClass")
    assert tid == "tenant:tenant-1:type:class:name:module.sub.MyClass"

    with pytest.raises(ValueError):
        canonical_typed_node_id("tenant-1", "", "name")
    with pytest.raises(ValueError):
        canonical_typed_node_id("tenant-1", "class", "")


def test_edge_weight_bounds_and_booleans():
    with pytest.raises(ValueError):
        RelationEdge(
            edge_id="e", tenant_id="t", source_id="s", target_id="tg", relationship_type="USES", weight=True  # type: ignore
        )
    with pytest.raises(ValueError):
        RelationEdge(
            edge_id="e", tenant_id="t", source_id="s", target_id="tg", relationship_type="USES", weight=-0.01
        )
    with pytest.raises(ValueError):
        RelationEdge(
            edge_id="e", tenant_id="t", source_id="s", target_id="tg", relationship_type="USES", weight=1.0001
        )

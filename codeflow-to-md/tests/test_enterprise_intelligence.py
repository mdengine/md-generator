from __future__ import annotations

from pathlib import Path

import networkx as nx
import pytest

from md_generator.codeflow.adapters import global_registry
from md_generator.codeflow.adapters.python import PythonAdapter
from md_generator.codeflow.cli.main import build_parser
from md_generator.codeflow.enterprise_ir.base import NodeType, EdgeType
from md_generator.codeflow.graph.enterprise_builder import (
    AliasRegistry,
    EnterpriseGraphBuilder,
    EntityRegistry,
    generate_stable_uri,
)
from md_generator.codeflow.graph.query import GraphQuery
from md_generator.codeflow.graph.traversal import GraphTraversal
from md_generator.codeflow.plugins.config.plugin import ConfigurationPlugin
from md_generator.codeflow.plugins.dependency.plugin import DependencyPlugin
from md_generator.codeflow.repository.model import Repository, Workspace


def test_registry_registration() -> None:
    adapter = global_registry.get_adapter_for_path(Path("foo.py"))
    assert adapter is not None
    assert isinstance(adapter, PythonAdapter)
    assert adapter.language == "python"


def test_stable_uri_generation() -> None:
    uri = generate_stable_uri(NodeType.CONFIG, "server.port")
    assert uri == "config://server.port"

    table_uri = generate_stable_uri(NodeType.TABLE, "employee")
    assert table_uri == "table://EMPLOYEE"


def test_alias_registry() -> None:
    reg = AliasRegistry()
    resolved = reg.resolve("javax.sql.DataSource")
    assert resolved == "DataSource"


def test_entity_registry() -> None:
    reg = EntityRegistry()
    reg.register("config://server.port", "node_1")
    assert reg.exists("config://server.port")
    assert reg.lookup("config://server.port") == "node_1"


def test_graph_builder_deduplication() -> None:
    g = nx.MultiDiGraph()
    builder = EnterpriseGraphBuilder(g, "scan-1", "test-repo", "main", "commit-1")
    
    # Insert node once
    nid1 = builder.build_node("config://server.port", NodeType.CONFIG, "python", "app.py", 10, {})
    # Insert node twice
    nid2 = builder.build_node("config://server.port", NodeType.CONFIG, "python", "app.py", 10, {})
    
    assert nid1 == nid2
    assert builder.nodes_created == 1
    assert builder.nodes_reused == 1
    assert g.has_node("config://server.port")


def test_graph_traversal() -> None:
    g = nx.MultiDiGraph()
    g.add_node("a")
    g.add_node("b")
    g.add_node("c")
    g.add_edge("a", "b", edge_type=EdgeType.CALLS.value)
    g.add_edge("b", "c", edge_type=EdgeType.CALLS.value)
    g.add_edge("c", "a", edge_type=EdgeType.CALLS.value)  # Cycle
    
    nodes = GraphTraversal.bfs(g, "a")
    assert "a" in nodes
    assert "b" in nodes
    assert "c" in nodes


def test_graph_query() -> None:
    g = nx.MultiDiGraph()
    g.add_node("config://port", kind="CONFIG", key="port")
    query = GraphQuery(g)
    configs = query.find_config()
    assert len(configs) == 1
    assert configs[0]["key"] == "port"


def test_cli_args_parsing() -> None:
    parser = build_parser()
    args = parser.parse_args(["scan", ".", "--config-analysis", "--max-traversal-depth", "10"])
    assert args.config_analysis is True
    assert args.max_traversal_depth == 10


def test_semantic_placeholders() -> None:
    from md_generator.codeflow.enterprise_ir.semantic import (
        SemanticEntity,
        SemanticRelation,
        SemanticGroup,
        SemanticCluster,
        SemanticTag,
    )
    from md_generator.codeflow.enterprise_ir.base import NodeMetadata, NodeType

    meta = NodeMetadata(
        id="sem-1",
        kind=NodeType.CLASS,
        language="python",
        repository="test-repo",
        module=None,
        file="foo.py",
        line=1,
        column=0,
        confidence="HIGH",
        parser="test",
        backend="test",
    )
    entity = SemanticEntity(id="sem-1", metadata=meta, embedding_vector=[0.1, 0.2], cluster_id=3)
    assert entity.id == "sem-1"
    assert entity.embedding_vector == [0.1, 0.2]
    assert entity.cluster_id == 3

    relation = SemanticRelation(id="rel-1", metadata=meta, source_id="a", target_id="b", similarity_score=0.85)
    assert relation.source_id == "a"
    assert relation.similarity_score == 0.85

    group = SemanticGroup(id="group-1", metadata=meta, group_name="auth", entity_ids=["a", "b"])
    assert group.group_name == "auth"
    assert group.entity_ids == ["a", "b"]

    cluster = SemanticCluster(id="cluster-1", metadata=meta, cluster_id=1, centroid=[0.5, 0.6])
    assert cluster.cluster_id == 1
    assert cluster.centroid == [0.5, 0.6]

    tag = SemanticTag(id="tag-1", metadata=meta, tag_name="deprecated", tagged_entities=["a"])
    assert tag.tag_name == "deprecated"


def test_embedding_layer() -> None:
    from md_generator.codeflow.enterprise_ir.embedding import (
        EmbeddingMetadata,
        EmbeddingResult,
        EmbeddingProvider,
        EmbeddingStorage,
    )

    meta = EmbeddingMetadata(model_name="test-model", dimension=128, metric="cosine", created_at="2026-06-23")
    result = EmbeddingResult(entity_id="node-1", vector=[0.1, 0.9], metadata=meta)
    assert result.entity_id == "node-1"
    assert result.metadata.dimension == 128


def test_runtime_correlator() -> None:
    from md_generator.codeflow.runtime.correlator import RuntimeTrace, RuntimeSession, RuntimeCorrelator
    from md_generator.codeflow.enterprise_ir.runtime import RuntimeEvent

    g = nx.MultiDiGraph()
    g.add_node("entity://method/UserService.login")
    
    correlator = RuntimeCorrelator(g)
    event = RuntimeEvent(event_name="UserService.login", timestamp="2026-06-23T12:00:00Z", duration_ms=25.0)
    trace = RuntimeTrace(trace_id="trace-1", events=[event])
    session = RuntimeSession(session_id="session-1", traces=[trace])
    
    correlation = correlator.correlate(session)
    assert "UserService.login" in correlation
    assert "entity://method/UserService.login" in correlation["UserService.login"]["static_nodes"]
    assert correlation["UserService.login"]["duration_ms"] == 25.0


def test_decoupled_annotation_plugins() -> None:
    from md_generator.codeflow.plugins import global_plugin_registry
    from md_generator.codeflow.plugins.classification.plugin import ClassificationPlugin
    from md_generator.codeflow.plugins.annotation.plugin import AnnotationPlugin
    from md_generator.codeflow.plugins.semantic.plugin import SemanticPlugin

    p_classif = global_plugin_registry.get_plugin("classification")
    p_annot = global_plugin_registry.get_plugin("annotation")
    p_sem = global_plugin_registry.get_plugin("semantic_plugin")

    assert p_classif is not None
    assert p_annot is not None
    assert p_sem is not None

    inst = p_classif()
    assert inst.metadata.name == "classification"
    assert inst.discover(None) == []


def test_business_architecture_models() -> None:
    from md_generator.codeflow.plugins.business.models import (
        CapabilityEntity,
        BusinessProcess,
        BusinessService,
        DomainModel,
        BusinessRule,
    )
    from md_generator.codeflow.enterprise_ir.base import NodeMetadata, NodeType

    meta = NodeMetadata(
        id="biz-1",
        kind=NodeType.CLASS,
        language="python",
        repository="test-repo",
        module=None,
        file="foo.py",
        line=1,
        column=0,
        confidence="HIGH",
        parser="test",
        backend="test",
    )
    cap = CapabilityEntity(id="biz-1", metadata=meta, capability_name="PaymentProcessing", business_domain="Finance")
    assert cap.capability_name == "PaymentProcessing"

    proc = BusinessProcess(id="biz-2", metadata=meta, process_name="CheckoutFlow", steps=["api://step1", "api://step2"])
    assert proc.process_name == "CheckoutFlow"
    assert proc.steps == ["api://step1", "api://step2"]


def test_lifecycle_hooks() -> None:
    # Verify hooks exist and run
    g = nx.MultiDiGraph()
    builder = EnterpriseGraphBuilder(g, "scan-1", "test-repo", "main", "commit-1")
    
    # Check hook definitions
    assert hasattr(builder, "_before_build_graph")
    assert hasattr(builder, "_after_build_graph")
    assert hasattr(builder, "_enrich_graph")
    assert hasattr(builder, "_enrich_semantics")
    assert hasattr(builder, "_correlate_runtime")
    assert hasattr(builder, "_finalize_graph")
    
    # We can override hooks to assert they are called
    called = []
    builder._enrich_graph = lambda: called.append("enrich_graph")
    builder._finalize_graph = lambda: called.append("finalize_graph")
    
    from md_generator.codeflow.enterprise_ir.graph import EnterpriseIR
    ir = EnterpriseIR()
    builder.merge_ir(ir)
    
    assert "enrich_graph" in called
    assert "finalize_graph" in called


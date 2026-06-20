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
from md_generator.codeflow.repository.model import Repository, Workspace, WorkspaceNode


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

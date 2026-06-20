from __future__ import annotations

import datetime
from typing import Any

import networkx as nx

from md_generator.codeflow.enterprise_ir.base import (
    GRAPH_SCHEMA_VERSION,
    EdgeMetadata,
    EdgeType,
    NodeMetadata,
    NodeType,
)
from md_generator.codeflow.enterprise_ir.graph import EnterpriseIR


def generate_stable_uri(kind: NodeType, name: str, details: str | None = None) -> str:
    """Generates a stable, deterministic URI based on NodeType and entity name."""
    s = name.strip()
    if kind == NodeType.CONFIG:
        return f"config://{s}"
    elif kind == NodeType.DEPENDENCY:
        return f"dependency://{s.lower()}"
    elif kind == NodeType.TABLE:
        return f"table://{s.upper()}"
    elif kind == NodeType.COLUMN:
        return f"column://{s.upper()}"
    elif kind == NodeType.QUEUE:
        return f"queue://{s.lower()}"
    elif kind == NodeType.TOPIC:
        return f"topic://{s.lower()}"
    elif kind == NodeType.STORAGE:
        return f"storage://{s.lower()}"
    elif kind == NodeType.RESOURCE:
        det = f"/{details.strip('/')}" if details else ""
        return f"resource://{s.lower()}{det}"
    elif kind == NodeType.API:
        det = f"/{details.strip('/')}" if details else ""
        return f"api://{s.upper()}{det}"
    return f"entity://{kind.value.lower()}/{s}"


class AliasRegistry:
    def __init__(self) -> None:
        self._aliases: dict[str, str] = {
            "javax.sql.DataSource": "DataSource",
            "com.mongodb.MongoClient": "MongoClient",
            "org.apache.kafka.clients.producer.KafkaProducer": "KafkaProducer",
        }

    def resolve(self, name: str) -> str:
        return self._aliases.get(name, name)

    def add_alias(self, alias_name: str, target_name: str) -> None:
        self._aliases[alias_name] = target_name


class EntityRegistry:
    def __init__(self) -> None:
        self._registry: dict[str, str] = {}  # URI -> Node ID

    def register(self, uri: str, node_id: str) -> None:
        self._registry[uri] = node_id

    def lookup(self, uri: str) -> str | None:
        return self._registry.get(uri)

    def exists(self, uri: str) -> bool:
        return uri in self._registry


class GraphSchemaValidator:
    @staticmethod
    def validate_node(node_id: str, kind: NodeType, attrs: dict[str, Any]) -> bool:
        # Check standard fields exist
        required = ["kind", "language", "repository", "file", "confidence", "version"]
        for r in required:
            if r not in attrs:
                return False
        return attrs["kind"] == kind.value

    @staticmethod
    def validate_edge(source: str, target: str, edge_type: EdgeType, attrs: dict[str, Any]) -> bool:
        required = ["edge_type", "confidence", "parser", "plugin", "version"]
        for r in required:
            if r not in attrs:
                return False
        return attrs["edge_type"] == edge_type.value


class EnterpriseGraphBuilder:
    def __init__(
        self,
        graph: nx.MultiDiGraph,
        scan_id: str,
        repository: str,
        branch: str,
        commit: str,
    ) -> None:
        self.graph = graph
        self.scan_id = scan_id
        self.repository = repository
        self.branch = branch
        self.commit = commit
        self.entity_registry = EntityRegistry()
        self.alias_registry = AliasRegistry()
        
        # Track statistics
        self.nodes_created = 0
        self.nodes_reused = 0
        self.edges_created = 0

        # Set graph-level metadata
        self.graph.graph["scan_id"] = self.scan_id
        self.graph.graph["repository"] = self.repository
        self.graph.graph["branch"] = self.branch
        self.graph.graph["commit"] = self.commit
        self.graph.graph["schema_version"] = GRAPH_SCHEMA_VERSION

    def build_node(self, uri: str, kind: NodeType, language: str, file_path: str, line: int | None, attributes: dict[str, Any]) -> str:
        resolved_uri = self.alias_registry.resolve(uri)
        if self.entity_registry.exists(resolved_uri):
            node_id = self.entity_registry.lookup(resolved_uri)
            self.nodes_reused += 1
            return node_id  # type: ignore

        node_id = resolved_uri
        self.graph.add_node(
            node_id,
            id=node_id,
            kind=kind.value,
            language=language,
            repository=self.repository,
            module=None,
            file=file_path,
            line=line,
            column=0,
            confidence="HIGH",
            parser="graph_builder",
            backend="native",
            version="1.0.0",
            scan_id=self.scan_id,
            branch=self.branch,
            commit=self.commit,
            schema_version=GRAPH_SCHEMA_VERSION,
            **attributes,
        )
        self.entity_registry.register(resolved_uri, node_id)
        self.nodes_created += 1
        return node_id

    def build_edge(self, source_id: str, target_id: str, edge_type: EdgeType, parser: str, plugin: str, language: str, confidence: str = "HIGH") -> None:
        # Check if identical edge already exists
        exists = False
        if self.graph.has_edge(source_id, target_id):
            for key, data in self.graph[source_id][target_id].items():
                if data.get("edge_type") == edge_type.value:
                    exists = True
                    break
        if exists:
            return

        self.graph.add_edge(
            source_id,
            target_id,
            edge_type=edge_type.value,
            confidence=confidence,
            parser=parser,
            plugin=plugin,
            language=language,
            created_by="central_graph_builder",
            timestamp=datetime.datetime.utcnow().isoformat(),
            version="1.0.0",
            scan_id=self.scan_id,
            branch=self.branch,
            commit=self.commit,
        )
        self.edges_created += 1

    def merge_ir(self, ir: EnterpriseIR) -> None:
        """Merges all packages in EnterpriseIR to build Graph nodes and edge relationships."""
        # 1. Configs
        for cfg in ir.configs:
            node_id = self.build_node(
                uri=cfg.id,
                kind=NodeType.CONFIG,
                language=cfg.metadata.language,
                file_path=cfg.source,
                line=cfg.line,
                attributes={
                    "key": cfg.key,
                    "value": cfg.value,
                    "type_name": cfg.type_name,
                    "usage_status": cfg.usage_status,
                },
            )

        # 2. Dependencies
        for dep in ir.dependencies:
            self.build_node(
                uri=dep.id,
                kind=NodeType.DEPENDENCY,
                language=dep.metadata.language,
                file_path=dep.metadata.file,
                line=None,
                attributes={
                    "name": dep.name,
                    "version": dep.version,
                    "scope": dep.scope,
                    "dependency_type": dep.dependency_type,
                },
            )

        # 3. Tables & Columns
        for tbl in ir.tables:
            self.build_node(
                uri=tbl.id,
                kind=NodeType.TABLE,
                language=tbl.metadata.language,
                file_path=tbl.metadata.file,
                line=None,
                attributes={
                    "table_name": tbl.table_name,
                    "database_type": tbl.database_type,
                },
            )

        # 4. Queries
        for qy in ir.queries:
            q_node = self.build_node(
                uri=qy.id,
                kind=NodeType.QUERY,
                language=qy.metadata.language,
                file_path=qy.source_file,
                line=qy.line_number,
                attributes={
                    "query_text": qy.query_text,
                    "operation": qy.operation,
                    "database_type": qy.database_type,
                    "dialect": qy.dialect,
                },
            )
            # Create relationships to tables
            for tbl in qy.tables_referenced:
                t_node = generate_stable_uri(NodeType.TABLE, tbl)
                self.build_edge(
                    source_id=q_node,
                    target_id=t_node,
                    edge_type=EdgeType.READS_TABLE if qy.operation == "READ" else EdgeType.WRITES_TABLE,
                    parser=qy.metadata.parser,
                    plugin="query_plugin",
                    language=qy.metadata.language,
                )

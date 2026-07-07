# Codeflow Enterprise Intelligence Layer: Guide & Reference

This documentation describes the architecture, schemas, and interfaces of Codeflow's **Enterprise Intelligence Layer**.

---

## 1. Graph Schema Specification

The graph uses a deterministic schema (v1.0) stored as node and edge properties inside JSON outputs and `graph.db`.

### Node Types
* `FILE`: Represent source code or configuration files.
* `CONFIG`: Represents properties keys (e.g. `config://server.port`).
* `DEPENDENCY`: Represents libraries/packages (e.g. `dependency://spring-boot`).
* `QUERY`: Database statements (SQL/NoSQL).
* `TABLE`: Database tables.
* `COLUMN`: Database columns.
* `VIEW`: Database views.
* `QUEUE`: Message queues.
* `TOPIC`: Event topics.
* `RESOURCE`: Client/outbound connectors (e.g. REST, S3, gRPC).
* `API`: Endpoint entry points.

### Edge Types
* `CALLS`: Call graph invocation.
* `USES_CONFIGURATION`: Code elements reading config keys.
* `READS_TABLE` / `WRITES_TABLE`: Database query targets.
* `PUBLISHES_EVENT` / `CONSUMES_EVENT`: Pub/sub handlers.
* `FILE_DEPENDS_ON`: Sibling imports.

---

## 2. Plugin Development Guide

All plugins reside in `plugins/` and subclass `BasePlugin`. They follow a strict lifecycle of discovery, parsing, normalization, validation, post-processing, and IR mapping.

```python
from md_generator.codeflow.plugins.base import BasePlugin, PluginMetadata
from md_generator.codeflow.enterprise_ir.base import PluginCategory

class CustomPlugin(BasePlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="custom",
            category=PluginCategory.PARSER,
            depends_on=["configuration"]
        )
```

---

## 3. Language & Framework Adapters

Adapters separate parser backends (native vs treesitter vs regex) from general codeflow scans.
All language adapters inherit from `LanguageAdapter` ABC and list supported backends in order of priority.

### Framework Extractor Hook
Frameworks hooks register against adapters using the `FrameworkExtractor` interface, letting developers add support for specific microservices packages without code changes.

---

## 4. GraphQuery & Traversal Guides

To fetch nodes or evaluate ancestor impact, exporters execute queries using the central `GraphQuery` and `GraphTraversal` interfaces:

```python
# BFS traversal
nodes = GraphTraversal.bfs(graph, start_node, max_depth=5)

# Queries
query = GraphQuery(graph)
configs = query.find_config()
```
Exporters are consolidated under the central `EnterpriseExporter` pipeline.

---

## 5. CLI & Configuration parameters

Enable selective scans using command line parameters:
* `--config-analysis`: Inspects property files and usage.
* `--dependency-analysis`: Inspects package manifest files.
* `--query-analysis`: Inspects SQL/NoSQL statements.
* `--external-analysis`: Inspects outbound resources.
* `--repository-analysis`: Generates metrics summaries.
* `--max-traversal-depth <N>`: Sets depth cutoff limits.

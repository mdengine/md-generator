# `md_generator.graph` API Reference

## Summary

| Item | Value |
|------|-------|
| Purpose | Convert Neo4j or NetworkX GraphML/GML to Node/relationship Markdown, Mermaid, Graphviz |
| CLI | `md-graph` |
| Extra | `graph` |
| Tier | `medium` |

## Quick CLI reference

| Argument | Type | Required | Default | Choices | Help |
| --- | --- | --- | --- | --- | --- |
| `--config` | Path | optional | None | — | Path to YAML config |
| `--source` | str | optional | None | ('networkx', 'neo4j') | — |
| `--uri` | str | optional | None | — | — |
| `--user` | str | optional | None | — | — |
| `--password` | str | optional | None | — | — |
| `--database` | str | optional | None | — | Neo4j database name (e.g. neo4j); passed to driver session(database=...) |
| `--graph-file` | Path | optional | None | — | — |
| `--depth` | int | optional | None | — | — |
| `--start-node` | str | optional | None | — | — |
| `--max-nodes` | int | optional | None | — | — |
| `--max-edges` | int | optional | None | — | — |
| `--output` | Path | optional | None | — | — |
| `--neo4j-id-mode` | str | optional | None | ('element_id', 'internal_id') | — |
| `--async` | flag | optional | false | — | Enqueue background job (prints job_id; uses SQLite job store) |
| `--markdown-layout` | str | optional | None | ('combined', 'individual') | combined (default): nodes.md, relationship.md, graph_summary with embedded sections; individual: nodes/ and relationships/ per entity |


## Primary symbols

| Symbol | Kind | Notes |
| --- | --- | --- |
| extract_to_markdown | callable | — |
| Neo4jAdapter | callable | — |
| GraphRunConfig | callable | — |


## Python API (mkdocstrings)

::: md_generator.graph
    options:
      show_source: false
      show_root_heading: true
      show_signature_annotations: true
      members_order: source
      filters:
        - "!^_"

# Graph Metadata CLI Reference

Command: **`md-graph`**  
Alternate: `mdengine graph-to-md`

## Arguments

| Name | Type | Required | Default | Choices | Description |
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
| `--individual` | flag | optional | false | — | Shortcut for --markdown-layout individual |
| `--viz` | flag | optional | false | — | Write output/graph/graph.dot and render PNG/SVG/PDF via Graphviz dot (if installed) |
| `--viz-formats` | str | optional | None | — | Comma-separated formats for --viz (default png,svg). Example: png,svg,pdf |
| `--no-mermaid` | flag | optional | false | — | Disable Mermaid diagram (graph/graph.mmd and README fenced block) |


## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime conversion failure |
| 2 | Invalid usage or missing input |

# Graph Metadata Responsibilities

## In scope

- neo4j
- networkx
- Graphviz

- Expose `md-graph` CLI for local and CI usage.
- Convert Neo4j or NetworkX GraphML/GML to Node/relationship Markdown, Mermaid, Graphviz.
- Provide FastAPI + optional MCP integration.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Mutating source databases (read-only metadata export).

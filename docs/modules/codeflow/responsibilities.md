# Codeflow Responsibilities

## In scope

- networkx
- javalang
- optional Celery/Redis workers
- sentence-transformers for semantic

- Expose `md-codeflow` CLI for local and CI usage.
- Convert Source repositories to Architecture Markdown, graphs, flow docs, JSON, Mermaid.
- Provide FastAPI + optional MCP integration.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.

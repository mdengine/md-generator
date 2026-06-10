# OData Metadata Responsibilities

## In scope

- httpx
- networkx
- pyyaml
- pydantic-settings

- Expose `md-odata` CLI for local and CI usage.
- Convert OData CSDL metadata (XML/JSON), folders, ZIP archives, or $metadata URLs to Entity catalog Markdown, optional graph and semantic chunks.
- Provide FastAPI + optional MCP integration.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.

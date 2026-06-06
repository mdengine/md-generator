# SAP Intelligence Responsibilities

## In scope

- networkx
- pyyaml
- pydantic
- httpx
- lxml
- governance module
- optional tree-sitter ABAP

- Expose `md-sap` CLI for local and CI usage.
- Convert ABAP, CDS, DDIC exports, OData, BAPI, IDoc, transport files to AI-ready SAP knowledge packs, graphs, governance, chunks.
- Provide FastAPI + optional MCP integration.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.

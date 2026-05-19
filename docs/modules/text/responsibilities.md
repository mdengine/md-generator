# Text JSON XML Responsibilities

## In scope

- xmltodict
- lxml

- Expose `md-text` CLI for local and CI usage.
- Convert TXT, JSON, XML to Readable Markdown representations.
- Provide FastAPI + optional MCP integration.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.

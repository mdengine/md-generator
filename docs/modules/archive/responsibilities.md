# ZIP Archive Responsibilities

## In scope

- nested pdf/word/ppt/xlsx/image converters

- Expose `md-zip` CLI for local and CI usage.
- Convert ZIP archives to Directory-oriented Markdown bundle.
- Provide FastAPI + optional MCP integration.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.

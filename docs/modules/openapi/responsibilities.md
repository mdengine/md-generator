# OpenAPI Responsibilities

## In scope

- prance
- openapi-spec-validator
- pyyaml

- Expose `md-openapi` CLI for local and CI usage.
- Convert OpenAPI 3.x or Swagger 2.0 to API documentation ZIP bundle.
- Provide FastAPI + optional MCP integration.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.

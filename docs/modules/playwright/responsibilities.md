# Playwright Web Capture Responsibilities

## In scope

- playwright
- Chromium browser binaries

- Expose `md-playwright` CLI for local and CI usage.
- Convert Rendered web pages and SPAs to Browser-captured Markdown.
- Provide FastAPI + optional MCP integration.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.

# URL and Web Responsibilities

## In scope

- httpx
- readability-lxml
- markdownify
- robots.txt

- Expose `md-url` CLI for local and CI usage.
- Convert HTTP(S) pages to Cleaned Markdown and optional artifacts.
- Provide FastAPI + optional MCP integration.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.

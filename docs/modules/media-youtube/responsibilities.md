# YouTube Responsibilities

## In scope

- youtube-transcript-api
- httpx

- Expose `md-youtube` CLI for local and CI usage.
- Convert YouTube URLs to Transcript and metadata Markdown.
- Provide FastAPI + optional MCP integration.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.

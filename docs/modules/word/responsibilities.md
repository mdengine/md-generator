# Word Responsibilities

## In scope

- mammoth
- markdownify

- Expose `md-word` CLI for local and CI usage.
- Convert DOCX documents to Markdown with optional embedded images.
- Provide FastAPI + optional MCP integration.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.

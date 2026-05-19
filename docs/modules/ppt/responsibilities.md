# PowerPoint Responsibilities

## In scope

- python-pptx
- embedded PDF/Word fallbacks
- OCR for images

- Expose `md-ppt` CLI for local and CI usage.
- Convert PPTX slide decks to Slide Markdown and extracted assets.
- Provide FastAPI + optional MCP integration.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.

# Image OCR Responsibilities

## In scope

- Pillow
- pytesseract
- paddleocr
- easyocr

- Expose `md-image` CLI for local and CI usage.
- Convert Image files or directories to OCR Markdown and metadata.
- Provide FastAPI + optional MCP integration.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.

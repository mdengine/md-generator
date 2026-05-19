# PDF Responsibilities

## In scope

- PyMuPDF
- pdfplumber
- optional Tesseract OCR

- Expose `md-pdf` CLI for local and CI usage.
- Convert PDF documents to Markdown with optional artifact layout and extracted images.
- Provide FastAPI + optional MCP integration.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.

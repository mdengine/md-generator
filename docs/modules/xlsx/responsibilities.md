# Excel and CSV Responsibilities

## In scope

- openpyxl

- Expose `md-xlsx` CLI for local and CI usage.
- Convert XLSX, XLSM, CSV to Worksheet or CSV Markdown tables.
- Provide FastAPI + optional MCP integration.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.

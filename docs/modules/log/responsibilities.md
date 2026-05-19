# Log Analysis Responsibilities

## In scope

- pandas
- scikit-learn
- optional sentence-transformers
- Chroma export

- Expose `md-log` CLI for local and CI usage.
- Convert Log files and uploads to Parsed events, summaries, incidents, optional clustering.
- Provide FastAPI + optional MCP integration.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.

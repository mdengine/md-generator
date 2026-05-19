# Database Metadata Responsibilities

## In scope

- SQLAlchemy
- psycopg2
- pymysql
- oracledb
- pymongo
- Graphviz
- mermaid-py

- Expose `md-db` CLI for local and CI usage.
- Convert Postgres, MySQL, Oracle, SQLite, Mongo, Access to Schema docs, ERD, Markdown ZIP.
- Provide FastAPI + optional MCP integration.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Mutating source databases (read-only metadata export).

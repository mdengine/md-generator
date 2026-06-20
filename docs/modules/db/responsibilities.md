# Database Metadata Responsibilities

## In scope

- SQLAlchemy
- psycopg2
- pymysql
- oracledb
- pymongo
- Graphviz
- mermaid-py
- Elasticsearch/OpenSearch REST API
- offline ES bundle ZIP upload

- Expose `md-db` CLI for local and CI usage.
- Convert Postgres, MySQL, Oracle, SQLite, Mongo, Access, Elasticsearch/OpenSearch clusters and offline JSON bundles to Schema docs, ERD, Markdown ZIP; Elasticsearch indices, templates, pipelines, ILM/SLM, search templates, alias and dependency graphs.
- Provide FastAPI + optional MCP integration.

## Elasticsearch export scope

When `database.type` is `elasticsearch`, optional features include indices, data streams, component/index templates, ingest pipelines, ILM/SLM policies, snapshot repositories, search templates, field caps, security placeholders, search architecture, and search dependency graph exports.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Mutating source databases (read-only metadata export).

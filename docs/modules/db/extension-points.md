# Database Metadata Extension Points

Database adapters in `db/adapters/` (factory pattern). Elasticsearch via `--type elasticsearch` or bundle upload to `/db-to-md/run/elasticsearch`.

## Safe extension patterns

- Add adapter implementations and register in factory modules.
- Add optional extras in `pyproject.toml` for heavy dependencies.
- Keep CLI/API thin — delegate to core functions for testability.

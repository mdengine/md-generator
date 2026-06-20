# Database Metadata Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `--config` | Path | optional | None | — | Path to YAML config |
| `--type` | str | optional | None | — | postgres\|mysql\|mssql\|oracle\|mongo\|sqlite\|access\|elasticsearch |
| `--uri` | str | optional | None | — | — |
| `--output` | Path | optional | None | — | — |
| `--include` | str | optional | None | — | Comma-separated feature list |
| `--exclude` | str | optional | None | — | — |
| `--schema` | str | optional | None | — | — |
| `--database` | str | optional | None | — | Mongo database name |
| `--index-pattern` | str | optional | None | — | Elasticsearch index pattern (stored in limits.index_pattern) |
| `--list-indices` | flag | optional | false | — | List index names for Elasticsearch and exit (alias for --list-schemas) |
| `--split-files` | str | optional | None | ('true', 'false') | — |
| `--workers` | int | optional | None | — | — |
| `--async` | flag | optional | false | — | Enqueue background job (prints job_id; uses SQLite job store) |
| `--erd-max-tables` | int | optional | None | — | ERD: max tables (default from config, usually 100) |
| `--erd-scope` | str | optional | None | ('full', 'per_schema', 'per_table') | ERD: full \| per_schema \| per_table |
| `--write-combined-feature-markdown` | str | optional | None | ('true', 'false') | When split_files, also write root tables.md, views.md, … bundles |
| `--readme-feature-merge` | str | optional | None | ('none', 'inline', 'toc') | Append combined bundle docs to README: none \| inline \| toc |
| `--test-connection` | flag | optional | false | — | Validate database connectivity and exit (no export) |
| `--list-schemas` | flag | optional | false | — | Print schema names (or catalog labels) and exit |
| `--output-format` | str | optional | 'text' | ('text', 'json') | Output format for --list-schemas |


## API routes (HTTP parameters)

| Method | Path | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| GET | /health | HTTP | — | — | FastAPI route |
| POST | /db-to-md/run/sqlite | HTTP | — | — | FastAPI route |
| POST | /db-to-md/job/sqlite | HTTP | — | — | FastAPI route |
| POST | /db-to-md/run/elasticsearch | HTTP | — | — | FastAPI route |
| POST | /db-to-md/job/elasticsearch | HTTP | — | — | FastAPI route |
| POST | /db-to-md/run/access | HTTP | — | — | FastAPI route |
| POST | /db-to-md/job/access | HTTP | — | — | FastAPI route |
| POST | /db-to-md/run | HTTP | — | — | FastAPI route |
| POST | /db-to-md/job | HTTP | — | — | FastAPI route |
| GET | /db-to-md/job/{job_id} | HTTP | — | — | FastAPI route |
| GET | /db-to-md/job/{job_id}/download | HTTP | — | — | FastAPI route |
| GET | /db-to-md/job/{job_id}/events | HTTP | — | — | FastAPI route |
| GET | /db-to-md/job/{job_id}/stream | HTTP | — | — | FastAPI route |


## Environment variables

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| DB_TO_MD_PORT | string/int | optional | varies | — | HTTP API listen port |


## Config files

| File | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| src\md_generator\db\config\default.yaml | YAML | optional | — | — | Packaged or preset config |


## YAML config keys (from packaged defaults)

| File | Key | Default / sample | Required | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| src\md_generator\db\config\default.yaml | database.type | 'postgres' | optional | — | From packaged YAML |
| src\md_generator\db\config\default.yaml | database.uri | 'postgresql://user:pass@localhost:5432/dbname' | optional | — | From packaged YAML |
| src\md_generator\db\config\default.yaml | database.schema | 'public' | optional | — | From packaged YAML |
| src\md_generator\db\config\default.yaml | output.path | './docs' | optional | — | From packaged YAML |
| src\md_generator\db\config\default.yaml | output.split_files | True | optional | — | From packaged YAML |
| src\md_generator\db\config\default.yaml | output.write_combined_feature_markdown | False | optional | — | From packaged YAML |
| src\md_generator\db\config\default.yaml | output.readme_feature_merge | 'none' | optional | — | From packaged YAML |
| src\md_generator\db\config\default.yaml | features.include | 'tables', 'views', 'indexes', 'procedures', ... | optional | — | From packaged YAML |
| src\md_generator\db\config\default.yaml | features.exclude | [] | optional | — | From packaged YAML |
| src\md_generator\db\config\default.yaml | execution.workers | 4 | optional | — | From packaged YAML |
| src\md_generator\db\config\default.yaml | limits.max_tables | 10000 | optional | — | From packaged YAML |
| src\md_generator\db\config\default.yaml | limits.max_collections | 500 | optional | — | From packaged YAML |
| src\md_generator\db\config\default.yaml | limits.sample_size | 50 | optional | — | From packaged YAML |
| src\md_generator\db\config\default.yaml | erd.max_tables | 100 | optional | — | From packaged YAML |
| src\md_generator\db\config\default.yaml | erd.scope | 'full' | optional | — | From packaged YAML |


## Run config dataclass fields

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| ErdConfig | max_tables | int | varies | 100 | Run config dataclass field |
| ErdConfig | scope | str | varies | 'full' | Run config dataclass field |
| RunConfig | db_type | str | varies | — | Run config dataclass field |
| RunConfig | uri | str | varies | — | Run config dataclass field |
| RunConfig | schema | str \| None | varies | None | Run config dataclass field |
| RunConfig | database | str \| None | varies | None | Run config dataclass field |
| RunConfig | output_path | Path | varies | field(default_factory=lambda: Path('docs')) | Run config dataclass field |
| RunConfig | split_files | bool | varies | True | Run config dataclass field |
| RunConfig | include | frozenset[str] | varies | field(default_factory=lambda: frozenset(FEATU... | Run config dataclass field |
| RunConfig | exclude | frozenset[str] | varies | field(default_factory=frozenset) | Run config dataclass field |
| RunConfig | workers | int | varies | 4 | Run config dataclass field |
| RunConfig | limits | dict[str, Any] | varies | field(default_factory=dict) | Run config dataclass field |
| RunConfig | erd | ErdConfig | varies | field(default_factory=ErdConfig) | Run config dataclass field |
| RunConfig | write_combined_feature_markdown | bool | varies | False | Run config dataclass field |
| RunConfig | readme_feature_merge | str | varies | 'none' | Run config dataclass field |
| RunConfig | write_manifest | bool | varies | True | Run config dataclass field |
| RunConfig | markdown_cross_links | bool | varies | True | Run config dataclass field |
| RunConfig | elasticsearch | ElasticsearchOutputConfig | varies | field(default_factory=ElasticsearchOutputConfig) | Run config dataclass field |
| RunConfig | security | RedactionConfig | varies | field(default_factory=RedactionConfig) | Run config dataclass field |


## Options / dataclass fields (sample)

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| AccessUploadOutputSection | path | str | varies | — | Field on options/config class |
| AccessUploadOutputSection | split_files | bool | varies | — | Field on options/config class |
| AccessUploadOutputSection | write_combined_feature_markdown | bool | varies | — | Field on options/config class |
| AccessUploadOutputSection | readme_feature_merge | Literal['none', 'inline', 'toc'] | varies | — | Field on options/config class |
| AccessUploadOutputSection | write_manifest | bool | varies | — | Field on options/config class |
| AccessUploadOutputSection | markdown_cross_links | bool | varies | — | Field on options/config class |
| AccessUploadFeaturesSection | include | list[str] \| None | varies | — | Field on options/config class |
| AccessUploadFeaturesSection | exclude | list[str] | varies | — | Field on options/config class |
| AccessUploadExecutionSection | workers | int | varies | — | Field on options/config class |
| AccessUploadErdSection | max_tables | int | varies | — | Field on options/config class |
| AccessUploadErdSection | scope | Literal['full', 'per_schema', 'per_table'] | varies | — | Field on options/config class |
| ElasticsearchUploadOutputSection | path | str | varies | — | Field on options/config class |
| ElasticsearchUploadOutputSection | split_files | bool | varies | — | Field on options/config class |
| ElasticsearchUploadOutputSection | write_combined_feature_markdown | bool | varies | — | Field on options/config class |
| ElasticsearchUploadOutputSection | readme_feature_merge | Literal['none', 'inline', 'toc'] | varies | — | Field on options/config class |
| ElasticsearchUploadOutputSection | write_manifest | bool | varies | — | Field on options/config class |
| ElasticsearchUploadOutputSection | markdown_cross_links | bool | varies | — | Field on options/config class |
| ElasticsearchUploadOutputSection | elasticsearch_mapping_mode | str \| None | varies | — | Field on options/config class |
| ElasticsearchUploadOutputSection | elasticsearch_include_raw_json | bool \| None | varies | — | Field on options/config class |
| ElasticsearchUploadOutputSection | elasticsearch_analyzer_format | str \| None | varies | — | Field on options/config class |
| ElasticsearchUploadFeaturesSection | include | list[str] \| None | varies | — | Field on options/config class |
| ElasticsearchUploadFeaturesSection | exclude | list[str] | varies | — | Field on options/config class |
| ElasticsearchUploadExecutionSection | workers | int | varies | — | Field on options/config class |
| DatabaseSection | type | str | varies | — | Field on options/config class |
| DatabaseSection | uri | str | varies | — | Field on options/config class |
| DatabaseSection | schema | str \| None | varies | — | Field on options/config class |
| DatabaseSection | database | str \| None | varies | — | Field on options/config class |
| OutputSection | path | str | varies | — | Field on options/config class |
| OutputSection | split_files | bool | varies | — | Field on options/config class |
| OutputSection | write_combined_feature_markdown | bool | varies | — | Field on options/config class |
| OutputSection | readme_feature_merge | Literal['none', 'inline', 'toc'] | varies | — | Field on options/config class |
| OutputSection | write_manifest | bool | varies | — | Field on options/config class |
| OutputSection | markdown_cross_links | bool | varies | — | Field on options/config class |
| OutputSection | elasticsearch_mapping_mode | str \| None | varies | — | Field on options/config class |
| OutputSection | elasticsearch_include_raw_json | bool \| None | varies | — | Field on options/config class |
| OutputSection | elasticsearch_analyzer_format | str \| None | varies | — | Field on options/config class |
| FeaturesSection | include | list[str] \| None | varies | — | Field on options/config class |
| FeaturesSection | exclude | list[str] | varies | — | Field on options/config class |
| ExecutionSection | workers | int | varies | — | Field on options/config class |
| ErdSection | max_tables | int | varies | — | Field on options/config class |


## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `db`.

# Log Analysis Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `--config` | Path | optional | None | — | YAML config path |
| `--input` | Path | optional | None | — | Log file or directory (repeatable) |
| `--output` | Path | optional | None | — | Output directory |
| `--preset` | str | optional | None | — | Parser preset name (e.g. generic, springboot, logback, json) |
| `--line-regex` | str | optional | None | — | Custom line regex (named groups: timestamp, level, message, …) |
| `--auto-detect` | flag | optional | false | — | Auto-detect parser preset from log sample |
| `--preset-dir` | str | optional | None | — | Directory with user preset YAML files (repeatable; also MD_LOG_PRESET_DIRS, ~/.mdengine/log/presets) |
| `--async` | flag | optional | false | — | Enqueue background job (prints job_id; SQLite job store) |
| `--export-jsonl` | flag | optional | false | — | Export embedding-ready JSONL chunks |
| `--export-parquet` | flag | optional | false | — | Export embedding-ready Parquet chunks |
| `--resume` | flag | optional | false | — | Enable incremental checkpoint resume |
| `--frontmatter` | flag | optional | false | — | Emit YAML frontmatter on artifacts |
| `--source` | str | optional | 'tail' | ['tail', 'stdin', 'kafka', 'redis', 'websocket'] | — |
| `--config` | Path | optional | None | — | — |
| `--input` | Path | optional | None | — | File path for tail source |
| `--output` | Path | optional | None | — | — |


## API routes (HTTP parameters)

| Method | Path | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| GET | /health | HTTP | — | — | FastAPI route |
| POST | /log-to-md/run | HTTP | — | — | FastAPI route |
| POST | /log-to-md/job | HTTP | — | — | FastAPI route |
| POST | /log-to-md/run/upload | HTTP | — | — | FastAPI route |
| POST | /log-to-md/job/upload | HTTP | — | — | FastAPI route |
| GET | /log-to-md/job/{job_id} | HTTP | — | — | FastAPI route |
| GET | /log-to-md/job/{job_id}/download | HTTP | — | — | FastAPI route |
| GET | /log-to-md/job/{job_id}/events | HTTP | — | — | FastAPI route |
| GET | /log-to-md/job/{job_id}/stream | HTTP | — | — | FastAPI route |


## Environment variables

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| LOG_TO_MD_PORT | string/int | optional | varies | — | HTTP API listen port |


## Config files

| File | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| src\md_generator\log\config\default.yaml | YAML | optional | — | — | Packaged or preset config |
| src\md_generator\log\config\presets\generic.yaml | YAML | optional | — | — | Packaged or preset config |
| src\md_generator\log\config\presets\json.yaml | YAML | optional | — | — | Packaged or preset config |
| src\md_generator\log\config\presets\logback.yaml | YAML | optional | — | — | Packaged or preset config |
| src\md_generator\log\config\presets\springboot.yaml | YAML | optional | — | — | Packaged or preset config |


## YAML config keys (from packaged defaults)

| File | Key | Default / sample | Required | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| src\md_generator\log\config\default.yaml | input.paths | [] | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | input.otel_path | null | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | parser.preset | 'generic' | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | parser.fuzzy_timestamp | False | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | parser.auto_detect | False | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | parser.preset_dirs | [] | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | normalization.redact_pii | False | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | normalization.normalize_numbers | False | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | normalization.normalize_uuid | False | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | normalization.normalize_paths | False | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | aggregation.timeline | 'hourly' | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | clustering.enabled | False | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | clustering.algorithm | 'kmeans' | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | clustering.n_clusters | 8 | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | clustering.random_state | 42 | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | clustering.max_features | 4096 | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | output.path | './log-docs' | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | output.split_by_level | True | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | output.generate_incidents | True | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | output.generate_clusters | False | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | output.generate_chunks | False | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | output.frontmatter | False | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | chunk.enabled | False | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | chunk.lines_per_chunk | 100000 | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | chunk.records_per_md_chunk | 500 | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | execution.workers | 4 | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | execution.max_lines_per_file | null | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | execution.encoding_fallbacks | 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252' | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | execution.batch_records | 10000 | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | execution.use_runtime | False | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | execution.distributed | False | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | plugins.enrichers | [] | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | incidents.min_occurrences | 2 | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | incidents.levels | 'ERROR', 'FATAL', 'WARN' | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | incidents.stacktrace_aware | True | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | chunking.enabled | False | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | chunking.strategies | 'incident', 'timeline', 'stacktrace', 'cluster', ... | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | chunking.chunk_id_namespace | 'chunk' | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | chunking.max_chunk_bytes | 256000 | optional | — | From packaged YAML |
| src\md_generator\log\config\default.yaml | embeddings.enabled | False | optional | — | From packaged YAML |


## Run config dataclass fields

_No entries detected._


## Options / dataclass fields (sample)

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| InputSectionModel | paths | list[str] | varies | — | Field on options/config class |
| InputSectionModel | otel_path | str \| None | varies | — | Field on options/config class |
| ParserSectionModel | preset | str | varies | — | Field on options/config class |
| ParserSectionModel | line_regex | str \| None | varies | — | Field on options/config class |
| ParserSectionModel | fuzzy_timestamp | bool | varies | — | Field on options/config class |
| ParserSectionModel | auto_detect | bool | varies | — | Field on options/config class |
| ParserSectionModel | preset_dirs | list[str] | varies | — | Field on options/config class |
| NormalizationSectionModel | redact_pii | bool | varies | — | Field on options/config class |
| NormalizationSectionModel | normalize_numbers | bool | varies | — | Field on options/config class |
| NormalizationSectionModel | normalize_uuid | bool | varies | — | Field on options/config class |
| NormalizationSectionModel | normalize_paths | bool | varies | — | Field on options/config class |
| AggregationSectionModel | timeline | Literal['none', 'hourly', 'daily'] | varies | — | Field on options/config class |
| ClusteringSectionModel | enabled | bool | varies | — | Field on options/config class |
| ClusteringSectionModel | algorithm | str | varies | — | Field on options/config class |
| ClusteringSectionModel | n_clusters | int | varies | — | Field on options/config class |
| ClusteringSectionModel | random_state | int | varies | — | Field on options/config class |
| ClusteringSectionModel | max_features | int | varies | — | Field on options/config class |
| OutputSectionModel | path | str | varies | — | Field on options/config class |
| OutputSectionModel | split_by_level | bool | varies | — | Field on options/config class |
| OutputSectionModel | generate_incidents | bool | varies | — | Field on options/config class |
| OutputSectionModel | generate_clusters | bool | varies | — | Field on options/config class |
| OutputSectionModel | generate_chunks | bool | varies | — | Field on options/config class |
| OutputSectionModel | frontmatter | bool | varies | — | Field on options/config class |
| ChunkSectionModel | enabled | bool | varies | — | Field on options/config class |
| ChunkSectionModel | lines_per_chunk | int | varies | — | Field on options/config class |
| ChunkSectionModel | records_per_md_chunk | int | varies | — | Field on options/config class |
| ExecutionSectionModel | workers | int | varies | — | Field on options/config class |
| ExecutionSectionModel | max_lines_per_file | int \| None | varies | — | Field on options/config class |
| ExecutionSectionModel | encoding_fallbacks | list[str] | varies | — | Field on options/config class |
| ExecutionSectionModel | batch_records | int | varies | — | Field on options/config class |
| ExecutionSectionModel | use_runtime | bool | varies | — | Field on options/config class |
| ExecutionSectionModel | distributed | bool | varies | — | Field on options/config class |
| IncrementalSectionModel | enabled | bool | varies | — | Field on options/config class |
| IncrementalSectionModel | checkpoint_path | str \| None | varies | — | Field on options/config class |
| StreamingSectionModel | enabled | bool | varies | — | Field on options/config class |
| StreamingSectionModel | source | str | varies | — | Field on options/config class |
| StreamingSectionModel | batch_size | int | varies | — | Field on options/config class |
| PluginsSectionModel | enrichers | list[str] | varies | — | Field on options/config class |
| InputSection | paths | list[str] | varies | — | Field on options/config class |
| InputSection | otel_path | str \| None | varies | — | Field on options/config class |


## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `log`.

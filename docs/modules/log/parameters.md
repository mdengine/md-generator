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


## Config file parameters

| File | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| src\md_generator\log\config\default.yaml | YAML | optional | — | — | Packaged or preset config |
| src\md_generator\log\config\presets\generic.yaml | YAML | optional | — | — | Packaged or preset config |
| src\md_generator\log\config\presets\json.yaml | YAML | optional | — | — | Packaged or preset config |
| src\md_generator\log\config\presets\logback.yaml | YAML | optional | — | — | Packaged or preset config |
| src\md_generator\log\config\presets\springboot.yaml | YAML | optional | — | — | Packaged or preset config |


## Options / dataclass fields (sample)

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| LogRunConfig | input | InputSection | varies | — | Field on options/config class |
| LogRunConfig | parser | ParserSection | varies | — | Field on options/config class |
| LogRunConfig | normalization | NormalizationSection | varies | — | Field on options/config class |
| LogRunConfig | aggregation | AggregationSection | varies | — | Field on options/config class |
| LogRunConfig | clustering | ClusteringSection | varies | — | Field on options/config class |
| LogRunConfig | output | OutputSection | varies | — | Field on options/config class |
| LogRunConfig | chunk | ChunkSection | varies | — | Field on options/config class |
| LogRunConfig | execution | ExecutionSection | varies | — | Field on options/config class |
| LogRunConfig | plugins | PluginsSection | varies | — | Field on options/config class |
| LogRunConfig | incidents | IncidentsSection | varies | — | Field on options/config class |
| LogRunConfig | chunking | ChunkingSection | varies | — | Field on options/config class |
| LogRunConfig | embeddings | EmbeddingsSection | varies | — | Field on options/config class |
| LogRunConfig | correlation | CorrelationSection | varies | — | Field on options/config class |
| LogRunConfig | knowledge_graph | KnowledgeGraphSection | varies | — | Field on options/config class |
| LogRunConfig | timeline | TimelineSection | varies | — | Field on options/config class |
| LogRunConfig | intelligence | IntelligenceSection | varies | — | Field on options/config class |
| LogRunConfig | search | SearchSection | varies | — | Field on options/config class |
| LogRunConfig | incremental | IncrementalSection | varies | — | Field on options/config class |
| LogRunConfig | ingestion | IngestionSection | varies | — | Field on options/config class |
| LogRunConfig | noise_reduction | NoiseReductionSection | varies | — | Field on options/config class |
| LogRunConfig | streaming | StreamingSection | varies | — | Field on options/config class |
| LogRunConfig | visualization | VisualizationSection | varies | — | Field on options/config class |
| LogRunConfig | documentation | DocumentationSection | varies | — | Field on options/config class |
| LogRunConfig | topology | TopologySection | varies | — | Field on options/config class |
| LogRunConfig | linking | LinkingSection | varies | — | Field on options/config class |
| LogRunConfig | governance | GovernanceSection | varies | — | Field on options/config class |


## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `log`.

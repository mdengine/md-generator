# OData Metadata Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `--file` | Path | optional | None | — | Path to metadata.xml/json |
| `--folder` | Path | optional | None | — | Directory containing OData metadata |
| `--zip` | Path | optional | None | — | ZIP archive containing metadata |
| `--url` | str | optional | [] | — | Fetch $metadata from URL (repeatable) |
| `--config` | Path | optional | None | — | YAML config |
| `--output` | Path | optional | None | — | Output directory |
| `--graph` | flag | optional | false | — | Export relationship graph |
| `--chunk` | flag | optional | false | — | Write semantic chunks |


## API routes (HTTP parameters)

| Method | Path | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| GET | /health | HTTP | — | — | FastAPI route |
| POST | /odata-to-md/generate | HTTP | — | — | FastAPI route |


## Environment variables

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| ODATA_TO_MD_PORT | string/int | optional | varies | — | HTTP API listen port |


## Config file parameters

| File | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| src\md_generator\odata\config\default.yaml | YAML | optional | — | — | Packaged or preset config |


## Options / dataclass fields (sample)

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| OdataGenerateOptions | graph | bool | varies | — | Field on options/config class |
| OdataGenerateOptions | chunks | bool | varies | — | Field on options/config class |
| OdataGenerateOptions | catalog | bool | varies | — | Field on options/config class |
| OdataRunConfig | file | Path \| None | varies | — | Field on options/config class |
| OdataRunConfig | folder | Path \| None | varies | — | Field on options/config class |
| OdataRunConfig | zip | Path \| None | varies | — | Field on options/config class |
| OdataRunConfig | urls | list[str] | varies | — | Field on options/config class |
| OdataRunConfig | output_path | Path | varies | — | Field on options/config class |
| OdataRunConfig | write_manifest | bool | varies | — | Field on options/config class |
| OdataRunConfig | features | FeaturesSection | varies | — | Field on options/config class |
| OdataRunConfig | odata | ODataFetchSection | varies | — | Field on options/config class |
| OdataRunConfig | chunking | ChunkingSection | varies | — | Field on options/config class |


## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `odata`.

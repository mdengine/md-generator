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


## Config files

| File | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| src\md_generator\odata\config\default.yaml | YAML | optional | — | — | Packaged or preset config |


## YAML config keys (from packaged defaults)

| File | Key | Default / sample | Required | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| src\md_generator\odata\config\default.yaml | input.file | null | optional | — | From packaged YAML |
| src\md_generator\odata\config\default.yaml | input.folder | null | optional | — | From packaged YAML |
| src\md_generator\odata\config\default.yaml | input.zip | null | optional | — | From packaged YAML |
| src\md_generator\odata\config\default.yaml | input.urls | [] | optional | — | From packaged YAML |
| src\md_generator\odata\config\default.yaml | output.path | 'output/odata-md' | optional | — | From packaged YAML |
| src\md_generator\odata\config\default.yaml | output.write_manifest | True | optional | — | From packaged YAML |
| src\md_generator\odata\config\default.yaml | features.catalog | True | optional | — | From packaged YAML |
| src\md_generator\odata\config\default.yaml | features.entities_json | True | optional | — | From packaged YAML |
| src\md_generator\odata\config\default.yaml | features.graph | False | optional | — | From packaged YAML |
| src\md_generator\odata\config\default.yaml | features.chunks | False | optional | — | From packaged YAML |
| src\md_generator\odata\config\default.yaml | odata.fetch_timeout_sec | 30 | optional | — | From packaged YAML |
| src\md_generator\odata\config\default.yaml | odata.verify_tls | True | optional | — | From packaged YAML |
| src\md_generator\odata\config\default.yaml | odata.cache_fetched | True | optional | — | From packaged YAML |
| src\md_generator\odata\config\default.yaml | chunking.types | 'odata_service', 'odata_entity_set', 'odata_capabilities', 'odata_index' | optional | — | From packaged YAML |


## Run config dataclass fields

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| ODataFetchSection | fetch_timeout_sec | int | varies | 30 | Run config dataclass field |
| ODataFetchSection | verify_tls | bool | varies | True | Run config dataclass field |
| ODataFetchSection | cache_fetched | bool | varies | True | Run config dataclass field |
| FeaturesSection | catalog | bool | varies | True | Run config dataclass field |
| FeaturesSection | entities_json | bool | varies | True | Run config dataclass field |
| FeaturesSection | graph | bool | varies | False | Run config dataclass field |
| FeaturesSection | chunks | bool | varies | False | Run config dataclass field |
| ChunkingSection | types | list[str] | varies | field(default_factory=lambda: ['odata_service... | Run config dataclass field |
| OdataRunConfig | file | Path \| None | varies | None | Run config dataclass field |
| OdataRunConfig | folder | Path \| None | varies | None | Run config dataclass field |
| OdataRunConfig | zip | Path \| None | varies | None | Run config dataclass field |
| OdataRunConfig | urls | list[str] | varies | field(default_factory=list) | Run config dataclass field |
| OdataRunConfig | output_path | Path | varies | field(default_factory=lambda: Path('output/od... | Run config dataclass field |
| OdataRunConfig | write_manifest | bool | varies | True | Run config dataclass field |
| OdataRunConfig | features | FeaturesSection | varies | field(default_factory=FeaturesSection) | Run config dataclass field |
| OdataRunConfig | odata | ODataFetchSection | varies | field(default_factory=ODataFetchSection) | Run config dataclass field |
| OdataRunConfig | chunking | ChunkingSection | varies | field(default_factory=ChunkingSection) | Run config dataclass field |


## Options / dataclass fields (sample)

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| OdataGenerateOptions | graph | bool | varies | — | Field on options/config class |
| OdataGenerateOptions | chunks | bool | varies | — | Field on options/config class |
| OdataGenerateOptions | catalog | bool | varies | — | Field on options/config class |
| ODataFetchSection | fetch_timeout_sec | int | varies | — | Field on options/config class |
| ODataFetchSection | verify_tls | bool | varies | — | Field on options/config class |
| ODataFetchSection | cache_fetched | bool | varies | — | Field on options/config class |
| FeaturesSection | catalog | bool | varies | — | Field on options/config class |
| FeaturesSection | entities_json | bool | varies | — | Field on options/config class |
| FeaturesSection | graph | bool | varies | — | Field on options/config class |
| FeaturesSection | chunks | bool | varies | — | Field on options/config class |
| ChunkingSection | types | list[str] | varies | — | Field on options/config class |
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

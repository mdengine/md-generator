# Text JSON XML Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `input` | Path | required | — | — | Input .txt, .json, or .xml path |
| `output` | Path | required | — | — | Output .md file or directory (with --artifact-layout) |
| `--artifact-layout` | flag | optional | false | — | Write document.md under output directory |
| `--encoding` | str | optional | 'utf-8' | — | Text encoding for input (default: utf-8) |
| `--format` | str | optional | 'auto' | ('auto', 'txt', 'json', 'xml') | Input format (default: auto from extension or sniff) |
| `--no-source-block` | flag | optional | false | — | Do not append original JSON/XML in a fenced code block |
| `--toc` | flag | optional | false | — | Insert a table of contents for JSON/XML section headings |
| `--structure` | str | optional | 'hierarchical' | ('hierarchical', 'flattened') | JSON/XML: nested headings (default) or flattened paths grouped as headings |
| `--xml-parser` | str | optional | 'auto' | ('auto', 'stdlib', 'lxml') | XML hierarchical mode only: parse with stdlib, lxml, or auto (prefer lxml if installed) |
| `-v` | flag | optional | false | — | — |


## API routes (HTTP parameters)

| Method | Path | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| POST | /convert/sync | HTTP | — | — | FastAPI route |
| POST | /convert/jobs | HTTP | — | — | FastAPI route |
| GET | /convert/jobs/{job_id} | HTTP | — | — | FastAPI route |
| GET | /convert/jobs/{job_id}/download | HTTP | — | — | FastAPI route |


## Environment variables

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| TXT_JSON_XML_TO_MD_PORT | string/int | optional | varies | — | HTTP API listen port |


## Config files

_No entries detected._


## YAML config keys (from packaged defaults)

_No entries detected._


## Run config dataclass fields

_No entries detected._


## Options / dataclass fields (sample)

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| ConvertOptions | artifact_layout | bool | varies | — | Field on options/config class |
| ConvertOptions | verbose | bool | varies | — | Field on options/config class |
| ConvertOptions | encoding | str | varies | — | Field on options/config class |
| ConvertOptions | input_format | InputFormat | varies | — | Field on options/config class |
| ConvertOptions | include_source_block | bool | varies | — | Field on options/config class |
| ConvertOptions | generate_toc | bool | varies | — | Field on options/config class |
| ConvertOptions | structure | StructureMode | varies | — | Field on options/config class |
| ConvertOptions | xml_parser | XmlParser | varies | — | Field on options/config class |


## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `text`.

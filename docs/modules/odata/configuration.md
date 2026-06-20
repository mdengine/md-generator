# OData Metadata Configuration

Configuration surfaces:

1. **CLI flags** — `md-odata --help`
2. **Environment variables** — see `parameters.md`
3. **Run config dataclasses** — `src/md_generator/odata/**/run_config.py`
4. **YAML presets** — `src\md_generator\odata\config\default.yaml`

## YAML keys (extracted defaults)

| Config file | Key | Default / sample |
| --- | --- | --- |
| src\md_generator\odata\config\default.yaml | input.file | null |
| src\md_generator\odata\config\default.yaml | input.folder | null |
| src\md_generator\odata\config\default.yaml | input.zip | null |
| src\md_generator\odata\config\default.yaml | input.urls | [] |
| src\md_generator\odata\config\default.yaml | output.path | 'output/odata-md' |
| src\md_generator\odata\config\default.yaml | output.write_manifest | True |
| src\md_generator\odata\config\default.yaml | features.catalog | True |
| src\md_generator\odata\config\default.yaml | features.entities_json | True |
| src\md_generator\odata\config\default.yaml | features.graph | False |
| src\md_generator\odata\config\default.yaml | features.chunks | False |
| src\md_generator\odata\config\default.yaml | odata.fetch_timeout_sec | 30 |
| src\md_generator\odata\config\default.yaml | odata.verify_tls | True |
| src\md_generator\odata\config\default.yaml | odata.cache_fetched | True |
| src\md_generator\odata\config\default.yaml | chunking.types | 'odata_service', 'odata_entity_set', 'odata_capabilities', 'odata_index' |


## Example

```bash
md-odata --help
```

For HTTP services, configure upload limits and CORS via module `settings.py` environment variables.

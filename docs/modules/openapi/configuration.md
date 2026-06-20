# OpenAPI Configuration

Configuration surfaces:

1. **CLI flags** — `md-openapi --help`
2. **Environment variables** — see `parameters.md`
3. **Run config dataclasses** — `src/md_generator/openapi/**/run_config.py`
4. **YAML presets** — `src\md_generator\openapi\config\default.yaml`

## YAML keys (extracted defaults)

| Config file | Key | Default / sample |
| --- | --- | --- |
| src\md_generator\openapi\config\default.yaml | input.file | null |
| src\md_generator\openapi\config\default.yaml | input.folder | null |
| src\md_generator\openapi\config\default.yaml | input.zip | null |
| src\md_generator\openapi\config\default.yaml | input.url | null |
| src\md_generator\openapi\config\default.yaml | output.path | './docs' |
| src\md_generator\openapi\config\default.yaml | output.formats | 'md', 'mermaid' |
| src\md_generator\openapi\config\default.yaml | openapi.preferred_media_type | 'application/json' |


## Example

```bash
md-openapi --help
```

For HTTP services, configure upload limits and CORS via module `settings.py` environment variables.

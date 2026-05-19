# OpenAPI Configuration

Configuration surfaces:

1. **CLI flags** — `md-openapi --help`
2. **Environment variables** — see `parameters.md`
3. **Python options classes** — under `src/md_generator/openapi`
4. **YAML presets** — `src\md_generator\openapi\config\default.yaml`

## Example

```bash
md-openapi --help
```

For HTTP services, configure upload limits and CORS via module `settings.py` environment variables.

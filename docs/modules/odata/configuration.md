# OData Metadata Configuration

Configuration surfaces:

1. **CLI flags** — `md-odata --help`
2. **Environment variables** — see `parameters.md`
3. **Python options classes** — under `src/md_generator/odata`
4. **YAML presets** — `src\md_generator\odata\config\default.yaml`

## Example

```bash
md-odata --help
```

For HTTP services, configure upload limits and CORS via module `settings.py` environment variables.

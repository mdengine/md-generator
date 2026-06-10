# SAP Intelligence Configuration

Configuration surfaces:

1. **CLI flags** — `md-sap --help`
2. **Environment variables** — see `parameters.md`
3. **Python options classes** — under `src/md_generator/sap`
4. **YAML presets** — `src\md_generator\sap\config\default.yaml`

## Example

```bash
md-sap --help
```

For HTTP services, configure upload limits and CORS via module `settings.py` environment variables.

# Database Metadata Configuration

Configuration surfaces:

1. **CLI flags** — `md-db --help`
2. **Environment variables** — see `parameters.md`
3. **Python options classes** — under `src/md_generator/db`
4. **YAML presets** — `src\md_generator\db\config\default.yaml`

## Example

```bash
md-db --help
```

For HTTP services, configure upload limits and CORS via module `settings.py` environment variables.

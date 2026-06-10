# OpenTelemetry Traces Configuration

Configuration surfaces:

1. **CLI flags** — `md-otel --help`
2. **Environment variables** — see `parameters.md`
3. **Python options classes** — under `src/md_generator/otel`
4. **YAML presets** — none packaged

## Example

```bash
md-otel --help
```

For HTTP services, configure upload limits and CORS via module `settings.py` environment variables.

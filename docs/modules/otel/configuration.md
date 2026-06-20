# OpenTelemetry Traces Configuration

Configuration surfaces:

1. **CLI flags** — `md-otel --help`
2. **Environment variables** — see `parameters.md`
3. **Run config dataclasses** — `src/md_generator/otel/**/run_config.py`
4. **YAML presets** — none packaged

## YAML keys (extracted defaults)

_No YAML keys detected._


## Example

```bash
md-otel --help
```

For HTTP services, configure upload limits and CORS via module `settings.py` environment variables.

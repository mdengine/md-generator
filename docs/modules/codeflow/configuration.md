# Codeflow Configuration

Configuration surfaces:

1. **CLI flags** — `md-codeflow --help`
2. **Environment variables** — see `parameters.md`
3. **Python options classes** — under `src/md_generator/codeflow`
4. **YAML presets** — none packaged

## Example

```bash
md-codeflow --help
```

For HTTP services, configure upload limits and CORS via module `settings.py` environment variables.

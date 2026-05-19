# YouTube Configuration

Configuration surfaces:

1. **CLI flags** — `md-youtube --help`
2. **Environment variables** — see `parameters.md`
3. **Python options classes** — under `src/md_generator/media/youtube`
4. **YAML presets** — none packaged

## Example

```bash
md-youtube --help
```

For HTTP services, configure upload limits and CORS via module `settings.py` environment variables.

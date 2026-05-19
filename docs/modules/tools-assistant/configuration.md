# AI Assistant Tools Configuration

Configuration surfaces:

1. **CLI flags** — `mdengine ai assist --help`
2. **Environment variables** — see `parameters.md`
3. **Python options classes** — under `src/md_generator/tools/assistant`
4. **YAML presets** — none packaged

## Example

```bash
mdengine ai assist --help
```

For HTTP services, configure upload limits and CORS via module `settings.py` environment variables.

# Skill Builder Configuration

Configuration surfaces:

1. **CLI flags** — `mdengine skill build --help`
2. **Environment variables** — see `parameters.md`
3. **Python options classes** — under `src/md_generator/tools/skill_builder`
4. **YAML presets** — none packaged

## Example

```bash
mdengine skill build --help
```

For HTTP services, configure upload limits and CORS via module `settings.py` environment variables.

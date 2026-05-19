# Graph Metadata Configuration

Configuration surfaces:

1. **CLI flags** — `md-graph --help`
2. **Environment variables** — see `parameters.md`
3. **Python options classes** — under `src/md_generator/graph`
4. **YAML presets** — `src\md_generator\graph\config\default.yaml`

## Example

```bash
md-graph --help
```

For HTTP services, configure upload limits and CORS via module `settings.py` environment variables.

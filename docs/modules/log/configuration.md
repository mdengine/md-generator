# Log Analysis Configuration

Configuration surfaces:

1. **CLI flags** — `md-log --help`
2. **Environment variables** — see `parameters.md`
3. **Python options classes** — under `src/md_generator/log`
4. **YAML presets** — `src\md_generator\log\config\default.yaml`, `src\md_generator\log\config\presets\generic.yaml`, `src\md_generator\log\config\presets\json.yaml`, `src\md_generator\log\config\presets\logback.yaml`, `src\md_generator\log\config\presets\springboot.yaml`

## Example

```bash
md-log --help
```

For HTTP services, configure upload limits and CORS via module `settings.py` environment variables.

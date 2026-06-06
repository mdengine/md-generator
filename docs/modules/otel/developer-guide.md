# OpenTelemetry Traces Developer Guide

## Layout

- Source: `src/md_generator/otel`
- Tests: `log-to-md/tests`
- Docs: `docs/modules/otel/`

## Local loop

```bash
pip install -e ".[dev,log-otel-proto,api]"
python -m pytest log-to-md/tests -q
md-otel --help
```

## Where to change behavior

- CLI parsing: `src\md_generator\otel\cli\main.py`
- Core logic: search `src/md_generator/otel` for `convert` / `extract` functions
- API routes: `N/A`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module otel`.

# OpenAPI Developer Guide

## Layout

- Source: `src/md_generator/openapi`
- Tests: `openapi-to-md/tests`
- Docs: `docs/modules/openapi/`

## Local loop

```bash
pip install -e ".[dev,openapi,api]"
python -m pytest openapi-to-md/tests -q
md-openapi --help
```

## Where to change behavior

- CLI parsing: `src\md_generator\openapi\cli\main.py`
- Core logic: search `src/md_generator/openapi` for `convert` / `extract` functions
- API routes: `src\md_generator\openapi\api\main.py`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module openapi`.

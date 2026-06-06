# OData Metadata Developer Guide

## Layout

- Source: `src/md_generator/odata`
- Tests: `odata-to-md/tests`
- Docs: `docs/modules/odata/`

## Local loop

```bash
pip install -e ".[dev,odata,api]"
python -m pytest odata-to-md/tests -q
md-odata --help
```

## Where to change behavior

- CLI parsing: `src\md_generator\odata\cli\main.py`
- Core logic: search `src/md_generator/odata` for `convert` / `extract` functions
- API routes: `src\md_generator\odata\api\main.py`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module odata`.

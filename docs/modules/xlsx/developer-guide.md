# Excel and CSV Developer Guide

## Layout

- Source: `src/md_generator/xlsx`
- Tests: `xlsx-to-md/tests`
- Docs: `docs/modules/xlsx/`

## Local loop

```bash
pip install -e ".[dev,xlsx,api]"
python -m pytest xlsx-to-md/tests -q
md-xlsx --help
```

## Where to change behavior

- CLI parsing: `src\md_generator\xlsx\converter.py`
- Core logic: search `src/md_generator/xlsx` for `convert` / `extract` functions
- API routes: `src\md_generator\xlsx\api\app.py`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module xlsx`.

# ZIP Archive Developer Guide

## Layout

- Source: `src/md_generator/archive`
- Tests: `zip-to-md/tests`
- Docs: `docs/modules/archive/`

## Local loop

```bash
pip install -e ".[dev,archive,api]"
python -m pytest zip-to-md/tests -q
md-zip --help
```

## Where to change behavior

- CLI parsing: `src\md_generator\archive\converter.py`
- Core logic: search `src/md_generator/archive` for `convert` / `extract` functions
- API routes: `src\md_generator\archive\api\main.py`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module archive`.

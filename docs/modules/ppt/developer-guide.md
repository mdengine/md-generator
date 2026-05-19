# PowerPoint Developer Guide

## Layout

- Source: `src/md_generator/ppt`
- Tests: `ppt-to-md/tests`
- Docs: `docs/modules/ppt/`

## Local loop

```bash
pip install -e ".[dev,ppt,api]"
python -m pytest ppt-to-md/tests -q
md-ppt --help
```

## Where to change behavior

- CLI parsing: `src\md_generator\ppt\converter.py`
- Core logic: search `src/md_generator/ppt` for `convert` / `extract` functions
- API routes: `src\md_generator\ppt\api\main.py`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module ppt`.

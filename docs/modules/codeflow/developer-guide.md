# Codeflow Developer Guide

## Layout

- Source: `src/md_generator/codeflow`
- Tests: `codeflow-to-md/tests`
- Docs: `docs/modules/codeflow/`

## Local loop

```bash
pip install -e ".[dev,codeflow,api]"
python -m pytest codeflow-to-md/tests -q
md-codeflow --help
```

## Where to change behavior

- CLI parsing: `src\md_generator\codeflow\cli\main.py`
- Core logic: search `src/md_generator/codeflow` for `convert` / `extract` functions
- API routes: `src\md_generator\codeflow\api\main.py`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module codeflow`.

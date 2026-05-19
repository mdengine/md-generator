# PDF Developer Guide

## Layout

- Source: `src/md_generator/pdf`
- Tests: `pdf-to-md/tests`
- Docs: `docs/modules/pdf/`

## Local loop

```bash
pip install -e ".[dev,pdf,api]"
python -m pytest pdf-to-md/tests -q
md-pdf --help
```

## Where to change behavior

- CLI parsing: `src\md_generator\pdf\converter.py`
- Core logic: search `src/md_generator/pdf` for `convert` / `extract` functions
- API routes: `src\md_generator\pdf\api\main.py`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module pdf`.

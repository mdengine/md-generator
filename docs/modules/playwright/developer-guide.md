# Playwright Web Capture Developer Guide

## Layout

- Source: `src/md_generator/playwright`
- Tests: `playwright-to-md/tests`
- Docs: `docs/modules/playwright/`

## Local loop

```bash
pip install -e ".[dev,playwright,api]"
python -m pytest playwright-to-md/tests -q
md-playwright --help
```

## Where to change behavior

- CLI parsing: `src\md_generator\playwright\cli.py`
- Core logic: search `src/md_generator/playwright` for `convert` / `extract` functions
- API routes: `src\md_generator\playwright\api\main.py`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module playwright`.

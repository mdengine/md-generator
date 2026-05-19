# Log Analysis Developer Guide

## Layout

- Source: `src/md_generator/log`
- Tests: `log-to-md/tests`
- Docs: `docs/modules/log/`

## Local loop

```bash
pip install -e ".[dev,log,api]"
python -m pytest log-to-md/tests -q
md-log --help
```

## Where to change behavior

- CLI parsing: `src\md_generator\log\cli\main.py`
- Core logic: search `src/md_generator/log` for `convert` / `extract` functions
- API routes: `src\md_generator\log\api\main.py`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module log`.

# AI Assistant Tools Developer Guide

## Layout

- Source: `src/md_generator/tools/assistant`
- Tests: `tool-assistant/tests`
- Docs: `docs/modules/tools-assistant/`

## Local loop

```bash
pip install -e ".[dev,skill-openai,api]"
python -m pytest tool-assistant/tests -q
mdengine ai assist --help
```

## Where to change behavior

- CLI parsing: `src\md_generator\tools\assistant\cli.py`
- Core logic: search `src/md_generator/tools/assistant` for `convert` / `extract` functions
- API routes: `N/A`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module tools-assistant`.

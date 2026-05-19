# Word Developer Guide

## Layout

- Source: `src/md_generator/word`
- Tests: `word-to-md/tests`
- Docs: `docs/modules/word/`

## Local loop

```bash
pip install -e ".[dev,word,api]"
python -m pytest word-to-md/tests -q
md-word --help
```

## Where to change behavior

- CLI parsing: `src\md_generator\word\converter.py`
- Core logic: search `src/md_generator/word` for `convert` / `extract` functions
- API routes: `src\md_generator\word\api\main.py`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module word`.

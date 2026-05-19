# Text JSON XML Developer Guide

## Layout

- Source: `src/md_generator/text`
- Tests: `txt-json-xml-to-md/tests`
- Docs: `docs/modules/text/`

## Local loop

```bash
pip install -e ".[dev,text,api]"
python -m pytest txt-json-xml-to-md/tests -q
md-text --help
```

## Where to change behavior

- CLI parsing: `src\md_generator\text\converter.py`
- Core logic: search `src/md_generator/text` for `convert` / `extract` functions
- API routes: `src\md_generator\text\api\main.py`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module text`.

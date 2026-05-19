# URL and Web Developer Guide

## Layout

- Source: `src/md_generator/url`
- Tests: `url-to-md/tests`
- Docs: `docs/modules/url/`

## Local loop

```bash
pip install -e ".[dev,url,api]"
python -m pytest url-to-md/tests -q
md-url --help
```

## Where to change behavior

- CLI parsing: `src\md_generator\url\converter.py`
- Core logic: search `src/md_generator/url` for `convert` / `extract` functions
- API routes: `src\md_generator\url\api\main.py`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module url`.

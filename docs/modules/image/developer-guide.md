# Image OCR Developer Guide

## Layout

- Source: `src/md_generator/image`
- Tests: `image-to-md/tests`
- Docs: `docs/modules/image/`

## Local loop

```bash
pip install -e ".[dev,image,api]"
python -m pytest image-to-md/tests -q
md-image --help
```

## Where to change behavior

- CLI parsing: `src\md_generator\image\converter.py`
- Core logic: search `src/md_generator/image` for `convert` / `extract` functions
- API routes: `src\md_generator\image\api\main.py`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module image`.

# YouTube Developer Guide

## Layout

- Source: `src/md_generator/media/youtube`
- Tests: `youtube-to-md/tests`
- Docs: `docs/modules/media-youtube/`

## Local loop

```bash
pip install -e ".[dev,youtube,api]"
python -m pytest youtube-to-md/tests -q
md-youtube --help
```

## Where to change behavior

- CLI parsing: `src\md_generator\media\youtube\converter.py`
- Core logic: search `src/md_generator/media/youtube` for `convert` / `extract` functions
- API routes: `src\md_generator\media\youtube\api\main.py`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module media-youtube`.

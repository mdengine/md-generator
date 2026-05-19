# Video Developer Guide

## Layout

- Source: `src/md_generator/media/video`
- Tests: `video-to-md/tests`
- Docs: `docs/modules/media-video/`

## Local loop

```bash
pip install -e ".[dev,video,api]"
python -m pytest video-to-md/tests -q
md-video --help
```

## Where to change behavior

- CLI parsing: `src\md_generator\media\video\converter.py`
- Core logic: search `src/md_generator/media/video` for `convert` / `extract` functions
- API routes: `src\md_generator\media\video\api\main.py`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module media-video`.

# Audio Developer Guide

## Layout

- Source: `src/md_generator/media/audio`
- Tests: `audio-to-md/tests`
- Docs: `docs/modules/media-audio/`

## Local loop

```bash
pip install -e ".[dev,audio,api]"
python -m pytest audio-to-md/tests -q
md-audio --help
```

## Where to change behavior

- CLI parsing: `src\md_generator\media\audio\converter.py`
- Core logic: search `src/md_generator/media/audio` for `convert` / `extract` functions
- API routes: `src\md_generator\media\audio\api\main.py`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module media-audio`.

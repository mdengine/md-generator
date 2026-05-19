# Audio Installation

## PyPI extra

```bash
pip install "mdengine[audio]"
```

## Editable development

```bash
pip install -e ".[audio,dev]"
```

## HTTP API support

```bash
pip install -e ".[audio,api]"
```

## System dependencies

| Dependency | When needed |
|------------|-------------|
| Python 3.10+ | Always |
| Graphviz `dot` | db/graph ERD or diagram rendering |
| Tesseract / OCR backends | image, ppt, archive nested OCR |
| ffmpeg / imageio-ffmpeg | audio/video |
| Playwright browsers | playwright (`playwright install chromium`) |

See [module README](https://github.com/vishal7090/md-generator/blob/main/audio-to-md/README.md) for module-specific notes.

# Word Installation

## PyPI extra

```bash
pip install "mdengine[word]"
```

## Editable development

```bash
pip install -e ".[word,dev]"
```

## HTTP API support

```bash
pip install -e ".[word,api]"
```

## System dependencies

| Dependency | When needed |
|------------|-------------|
| Python 3.10+ | Always |
| Graphviz `dot` | db/graph ERD or diagram rendering |
| Tesseract / OCR backends | image, ppt, archive nested OCR |
| ffmpeg / imageio-ffmpeg | audio/video |
| Playwright browsers | playwright (`playwright install chromium`) |

See [module README](https://github.com/vishal7090/md-generator/blob/main/word-to-md/README.md) for module-specific notes.

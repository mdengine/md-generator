# PDF Installation

## PyPI extra

```bash
pip install "mdengine[pdf]"
```

## Editable development

```bash
pip install -e ".[pdf,dev]"
```

## HTTP API support

```bash
pip install -e ".[pdf,api]"
```

## System dependencies

| Dependency | When needed |
|------------|-------------|
| Python 3.10+ | Always |
| Graphviz `dot` | db/graph ERD or diagram rendering |
| Tesseract / OCR backends | image, ppt, archive nested OCR |
| ffmpeg / imageio-ffmpeg | audio/video |
| Playwright browsers | playwright (`playwright install chromium`) |

See [module README](https://github.com/vishal7090/md-generator/blob/main/pdf-to-md/README.md) for module-specific notes.

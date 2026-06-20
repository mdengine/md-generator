# ZIP Archive Installation

## PyPI extra

```bash
pip install "mdengine[archive]"
```

## Editable development

```bash
pip install -e ".[archive plus nested format extras,dev]"
```

## HTTP API support

```bash
pip install -e ".[archive,api]"
```

## System dependencies

| Dependency | When needed |
|------------|-------------|
| Python 3.10+ | Always |
| Graphviz `dot` | db/graph ERD or diagram rendering |
| Tesseract / OCR backends | image, ppt, archive nested OCR |
| ffmpeg / imageio-ffmpeg | audio/video |
| Playwright browsers | playwright (`playwright install chromium`) |

See [module README](https://github.com/mdengine/md-generator/blob/main/zip-to-md/README.md) for module-specific notes.

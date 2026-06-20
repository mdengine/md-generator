# OData Metadata Installation

## PyPI extra

```bash
pip install "mdengine[odata]"
```

## Editable development

```bash
pip install -e ".[odata,dev]"
```

## HTTP API support

```bash
pip install -e ".[odata,api]"
```

## System dependencies

| Dependency | When needed |
|------------|-------------|
| Python 3.10+ | Always |
| Graphviz `dot` | db/graph ERD or diagram rendering |
| Tesseract / OCR backends | image, ppt, archive nested OCR |
| ffmpeg / imageio-ffmpeg | audio/video |
| Playwright browsers | playwright (`playwright install chromium`) |

See [module README](https://github.com/mdengine/md-generator/blob/main/odata-to-md/README.md) for module-specific notes.

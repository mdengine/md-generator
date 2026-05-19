# AI Assistant Tools Installation

## PyPI extra

```bash
pip install "mdengine[skill-openai]"
```

## Editable development

```bash
pip install -e ".[skill-openai or skill-rag-chroma,dev]"
```

## HTTP API support

```bash
pip install -e ".[skill-openai,api]"
```

## System dependencies

| Dependency | When needed |
|------------|-------------|
| Python 3.10+ | Always |
| Graphviz `dot` | db/graph ERD or diagram rendering |
| Tesseract / OCR backends | image, ppt, archive nested OCR |
| ffmpeg / imageio-ffmpeg | audio/video |
| Playwright browsers | playwright (`playwright install chromium`) |

See [module README](https://github.com/vishal7090/md-generator/blob/main/ai/README.md) for module-specific notes.

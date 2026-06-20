# OpenTelemetry Traces Installation

## PyPI extra

```bash
pip install "mdengine[log-otel-proto]"
```

## Editable development

```bash
pip install -e ".[log-otel-proto for protobuf,dev]"
```

## HTTP API support

```bash
pip install -e ".[log-otel-proto,api]"
```

## System dependencies

| Dependency | When needed |
|------------|-------------|
| Python 3.10+ | Always |
| Graphviz `dot` | db/graph ERD or diagram rendering |
| Tesseract / OCR backends | image, ppt, archive nested OCR |
| ffmpeg / imageio-ffmpeg | audio/video |
| Playwright browsers | playwright (`playwright install chromium`) |

See [module README](https://github.com/mdengine/md-generator/blob/main/example/otel/README.md) for module-specific notes.

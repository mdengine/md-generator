# OpenTelemetry Traces Examples

## CLI

```bash
pip install "mdengine[log-otel-proto]"
md-otel --help
```

## Python

```python
import md_generator.otel  # adjust import
# See entry functions: load_otlp_json, load_otlp_bytes
```

## HTTP

```bash
uvicorn md_generator.otel.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```

# OpenAPI Examples

## CLI

```bash
pip install "mdengine[openapi]"
md-openapi --help
```

## Python

```python
import md_generator.openapi  # adjust import
# See entry functions: extract_to_markdown, load_spec
```

## HTTP

```bash
uvicorn md_generator.openapi.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```

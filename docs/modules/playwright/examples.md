# Playwright Web Capture Examples

## CLI

```bash
pip install "mdengine[playwright]"
md-playwright --help
```

## Python

```python
import md_generator.playwright  # adjust import
# See entry functions: convert_url_to_md, PlaywrightOptions
```

## HTTP

```bash
uvicorn md_generator.playwright.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```

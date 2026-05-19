# URL and Web Examples

## CLI

```bash
pip install "mdengine[url]"
md-url --help
```

## Python

```python
import md_generator.url  # adjust import
# See entry functions: convert_url, run_crawl
```

## HTTP

```bash
uvicorn md_generator.url.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```

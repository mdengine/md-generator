# Log Analysis Examples

## CLI

```bash
pip install "mdengine[log]"
md-log --help
```

## Python

```python
import md_generator.log  # adjust import
# See entry functions: extract_to_markdown, run_pipeline
```

## HTTP

```bash
uvicorn md_generator.log.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```

# Database Metadata Examples

## CLI

```bash
pip install "mdengine[db]"
md-db --help
```

## Python

```python
import md_generator.db  # adjust import
# See entry functions: extract_to_markdown, create_adapter
```

## HTTP

```bash
uvicorn md_generator.db.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```

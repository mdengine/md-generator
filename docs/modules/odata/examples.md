# OData Metadata Examples

## CLI

```bash
pip install "mdengine[odata]"
md-odata --help
```

## Python

```python
import md_generator.odata  # adjust import
# See entry functions: extract_to_markdown, OdataRunConfig
```

## HTTP

```bash
uvicorn md_generator.odata.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```

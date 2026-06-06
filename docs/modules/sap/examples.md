# SAP Intelligence Examples

## CLI

```bash
pip install "mdengine[sap]"
md-sap --help
```

## Python

```python
import md_generator.sap  # adjust import
# See entry functions: extract_to_markdown, SapRunConfig
```

## HTTP

```bash
uvicorn md_generator.sap.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```

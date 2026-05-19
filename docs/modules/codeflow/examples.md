# Codeflow Examples

## CLI

```bash
pip install "mdengine[codeflow]"
md-codeflow --help
```

## Python

```python
import md_generator.codeflow  # adjust import
# See entry functions: run_scan, ScanConfig
```

## HTTP

```bash
uvicorn md_generator.codeflow.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```

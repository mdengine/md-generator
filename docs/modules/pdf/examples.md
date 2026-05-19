# PDF Examples

## CLI

```bash
pip install "mdengine[pdf]"
md-pdf --help
```

## Python

```python
import md_generator.pdf  # adjust import
# See entry functions: convert_pdf, convert_pdf_to_artifact_dir
```

## HTTP

```bash
uvicorn md_generator.pdf.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```

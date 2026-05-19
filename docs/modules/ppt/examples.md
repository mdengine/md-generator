# PowerPoint Examples

## CLI

```bash
pip install "mdengine[ppt]"
md-ppt --help
```

## Python

```python
import md_generator.ppt  # adjust import
# See entry functions: convert_pptx, ConvertOptions
```

## HTTP

```bash
uvicorn md_generator.ppt.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```

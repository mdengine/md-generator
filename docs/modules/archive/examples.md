# ZIP Archive Examples

## CLI

```bash
pip install "mdengine[archive]"
md-zip --help
```

## Python

```python
import md_generator.archive  # adjust import
# See entry functions: convert_archive, convert_zip
```

## HTTP

```bash
uvicorn md_generator.archive.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```

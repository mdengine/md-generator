# Image OCR Examples

## CLI

```bash
pip install "mdengine[image]"
md-image --help
```

## Python

```python
import md_generator.image  # adjust import
# See entry functions: convert_images, convert_images_recursive
```

## HTTP

```bash
uvicorn md_generator.image.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```

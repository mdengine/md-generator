# Audio Examples

## CLI

```bash
pip install "mdengine[audio]"
md-audio --help
```

## Python

```python
import md_generator.media.audio  # adjust import
# See entry functions: DocumentConverter, AudioConverter
```

## HTTP

```bash
uvicorn md_generator.media.audio.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```

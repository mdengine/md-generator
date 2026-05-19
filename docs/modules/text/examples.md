# Text JSON XML Examples

## CLI

```bash
pip install "mdengine[text]"
md-text --help
```

## Python

```python
import md_generator.text  # adjust import
# See entry functions: convert_text_file, json_to_markdown
```

## HTTP

```bash
uvicorn md_generator.text.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```

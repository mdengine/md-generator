# Word Examples

## CLI

```bash
pip install "mdengine[word]"
md-word --help
```

## Python

```python
import md_generator.word  # adjust import
# See entry functions: convert_docx_to_markdown, WordToMdSettings
```

## HTTP

```bash
uvicorn md_generator.word.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```

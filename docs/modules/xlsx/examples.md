# Excel and CSV Examples

## CLI

```bash
pip install "mdengine[xlsx]"
md-xlsx --help
```

## Python

```python
import md_generator.xlsx  # adjust import
# See entry functions: convert_excel_to_markdown, ConvertConfig
```

## HTTP

```bash
uvicorn md_generator.xlsx.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```

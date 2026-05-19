# AI Assistant Tools Examples

## CLI

```bash
pip install "mdengine[skill-openai]"
mdengine ai assist --help
```

## Python

```python
import md_generator.tools.assistant  # adjust import
# See entry functions: Registry, MasterAgent
```

## HTTP

```bash
uvicorn md_generator.tools.assistant.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```

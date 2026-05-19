# Graph Metadata Examples

## CLI

```bash
pip install "mdengine[graph]"
md-graph --help
```

## Python

```python
import md_generator.graph  # adjust import
# See entry functions: extract_to_markdown, Neo4jAdapter
```

## HTTP

```bash
uvicorn md_generator.graph.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```

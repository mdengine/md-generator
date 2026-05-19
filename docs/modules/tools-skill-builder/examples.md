# Skill Builder Examples

## CLI

```bash
pip install "mdengine[(base]"
mdengine skill build --help
```

## Python

```python
import md_generator.tools.skill_builder  # adjust import
# See entry functions: run_generate, build_dependency_graph
```

## HTTP

```bash
uvicorn md_generator.tools.skill_builder.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```

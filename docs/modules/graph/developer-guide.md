# Graph Metadata Developer Guide

## Layout

- Source: `src/md_generator/graph`
- Tests: `graph-to-md/tests`
- Docs: `docs/modules/graph/`

## Local loop

```bash
pip install -e ".[dev,graph,api]"
python -m pytest graph-to-md/tests -q
md-graph --help
```

## Where to change behavior

- CLI parsing: `src\md_generator\graph\cli\main.py`
- Core logic: search `src/md_generator/graph` for `convert` / `extract` functions
- API routes: `src\md_generator\graph\api\main.py`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module graph`.

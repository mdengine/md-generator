# Database Metadata Developer Guide

## Layout

- Source: `src/md_generator/db`
- Tests: `db-to-md/tests`
- Docs: `docs/modules/db/`

## Local loop

```bash
pip install -e ".[dev,db,api]"
python -m pytest db-to-md/tests -q
md-db --help
```

## Where to change behavior

- CLI parsing: `src\md_generator\db\cli\main.py`
- Core logic: search `src/md_generator/db` for `convert` / `extract` functions
- API routes: `src\md_generator\db\api\main.py`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module db`.

# SAP Intelligence Developer Guide

## Layout

- Source: `src/md_generator/sap`
- Tests: `sap-to-md/tests`
- Docs: `docs/modules/sap/`

## Local loop

```bash
pip install -e ".[dev,sap,api]"
python -m pytest sap-to-md/tests -q
md-sap --help
```

## Where to change behavior

- CLI parsing: `src\md_generator\sap\cli\main.py`
- Core logic: search `src/md_generator/sap` for `convert` / `extract` functions
- API routes: `src\md_generator\sap\api\main.py`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module sap`.

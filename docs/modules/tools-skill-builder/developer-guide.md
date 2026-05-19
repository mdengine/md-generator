# Skill Builder Developer Guide

## Layout

- Source: `src/md_generator/tools/skill_builder`
- Tests: `matching *-to-md/tests`
- Docs: `docs/modules/tools-skill-builder/`

## Local loop

```bash
pip install -e ".[dev,(base,api]"
python -m pytest -q
mdengine skill build --help
```

## Where to change behavior

- CLI parsing: `cli module`
- Core logic: search `src/md_generator/tools/skill_builder` for `convert` / `extract` functions
- API routes: `N/A`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module tools-skill-builder`.

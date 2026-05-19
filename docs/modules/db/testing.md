# Database Metadata Testing

```bash
python -m pytest db-to-md/tests -q
```

Tests live under `db-to-md/tests`.

CI currently runs a subset (see root `.github/workflows/ci.yml`); run full module tests locally before merging converter changes.

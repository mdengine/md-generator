# OpenAPI Testing

```bash
python -m pytest openapi-to-md/tests -q
```

Tests live under `openapi-to-md/tests`.

CI currently runs a subset (see root `.github/workflows/ci.yml`); run full module tests locally before merging converter changes.

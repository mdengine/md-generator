# Excel and CSV Testing

```bash
python -m pytest xlsx-to-md/tests -q
```

Tests live under `xlsx-to-md/tests`.

CI currently runs a subset (see root `.github/workflows/ci.yml`); run full module tests locally before merging converter changes.

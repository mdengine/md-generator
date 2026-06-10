# OpenTelemetry Traces Testing

```bash
python -m pytest log-to-md/tests -q
```

Tests live under `log-to-md/tests`.

CI currently runs a subset (see root `.github/workflows/ci.yml`); run full module tests locally before merging converter changes.

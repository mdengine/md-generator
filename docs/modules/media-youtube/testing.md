# YouTube Testing

```bash
python -m pytest youtube-to-md/tests -q
```

Tests live under `youtube-to-md/tests`.

CI currently runs a subset (see root `.github/workflows/ci.yml`); run full module tests locally before merging converter changes.

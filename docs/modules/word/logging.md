# Word Logging

- Use `-v` / `--verbose` on CLIs where available for stderr diagnostics.
- API modules log job lifecycle at INFO; enable uvicorn access logs in deployment.
- **Do not log secrets** (DB URIs, API keys). Pass via environment variables.
- For support, capture: module name, `md-word` argv (redacted), job id, and first stderr stack trace.

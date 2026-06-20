# Log Analysis Compatibility

| Item | Support |
|------|---------|
| Python | 3.10+ (per `pyproject.toml`) |
| OS | Windows, Linux, macOS (module-specific native deps may vary) |
| PyPI extra | `log` |
| Input | Log files, directories, OTLP sidecars, streaming sources (tail, Kafka, Redis, websocket, stdin) |

Test your target input versions in CI with fixtures under `log-to-md/tests`.

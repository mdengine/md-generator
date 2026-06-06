# OpenTelemetry Traces Architecture

## Internal layout

Source root: `src/md_generator/otel` (8 Python modules detected).

Subpackages and areas: `cli`.

## Component diagram

```mermaid
flowchart TB
    CLI[CLI_md-otel] --> Core[Core_engine]
    API[FastAPI_optional] --> Core
    Core --> Writers[Markdown_writers]
    Core --> Assets[Asset_handlers]
    Core --> Integrations[External_libraries]
```

## Dependency graph (logical)

- **Inputs:** OTLP JSON or protobuf trace exports
- **Outputs:** Trace summary Markdown (`trace.md`)
- **Optional extras:** `log-otel-proto for protobuf` from `pyproject.toml`
- **Cross-module:** See `integration.md` for delegated converters and shared job patterns.

## Threading and async

- CLI runs synchronously in the invoking process.
- FastAPI routes may use background tasks or threads for long jobs.
- Domain modules (`db`, `graph`, `log`, `codeflow`) expose SSE/event streams for progress.

## Data flow

```mermaid
flowchart LR
    Raw[Raw_input] --> Parse[Parse_or_load]
    Parse --> Model[Internal_representation]
    Model --> Emit[Markdown_emitter]
    Emit --> Out[Files_or_ZIP]
```

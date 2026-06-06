# OpenTelemetry Traces Responsibilities

## In scope

- opentelemetry-proto optional
- protobuf optional
- log utils for I/O

- Expose `md-otel` CLI for local and CI usage.
- Convert OTLP JSON or protobuf trace exports to Trace summary Markdown (`trace.md`).
- Operate as library/CLI tooling without HTTP surface.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.

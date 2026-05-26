# Examples — OpenTelemetry → Markdown

## CLI (JSON OTLP)

```bash
pip install mdengine
md-otel --input ./export.json --output ./otel-docs
```

## CLI (protobuf OTLP)

```bash
pip install "mdengine[log-otel-proto]"
md-otel --input ./export.pb --output ./otel-docs --protobuf
```

## Meta-router

```bash
mdengine otel-to-md --input ./export.json --output ./otel-docs
```

Output: `./otel-docs/trace.md` (span listing, capped at 500 spans in the summary).

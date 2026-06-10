# Examples — log → Markdown

## CLI (sync)

```bash
pip install "mdengine[log]"
md-log --input ./app.log --output ./log-md-out --preset generic
```

With explicit config:

```bash
md-log --config ./my-log-to-md.yaml --output ./out
```

## CLI (async job — prints `job_id`)

```bash
md-log --input ./big.log --output ./out --async
```

## Search exported log docs

After a run produces an indexed bundle under `./log-docs` (or your `--output`):

```bash
mdengine search "NullPointerException in payment service" --index ./log-docs
```

## API + MCP

```bash
pip install "mdengine[log,api,mcp]"
export LOG_TO_MD_PORT=8020
md-log-api
```

Then: `GET /health`, `POST /log-to-md/run` (JSON) or `POST /log-to-md/run/upload` (multipart). MCP: `http://127.0.0.1:8020/mcp`.

```bash
md-log-mcp --transport stdio
```

## Optional clustering / semantic extras

```bash
pip install "mdengine[log,log-cluster]"
# or (large): pip install "mdengine[log,log-semantic]"
```

## Streaming and export extras

```bash
pip install "mdengine[log,log-stream-kafka]"   # Kafka ingest
pip install "mdengine[log,log-stream-redis]"   # Redis streams
pip install "mdengine[log,log-stream-ws]"       # WebSocket ingest
pip install "mdengine[log,log-export-parquet]"  # Parquet sidecar export
```

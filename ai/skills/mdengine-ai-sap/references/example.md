# Examples — SAP → Markdown

## CLI (sync)

```bash
pip install "mdengine[sap]"
md-sap ./sap-sources --output ./sap-md-out --include-cds --graph
```

With explicit config:

```bash
md-sap --config ./my-sap-to-md.yaml --output ./out
```

## CLI (async job — prints `job_id`)

```bash
md-sap ./large-repo --output ./out --async
```

## API + MCP

```bash
pip install "mdengine[sap,api,mcp]"
export SAP_TO_MD_PORT=8020
md-sap-api --host 127.0.0.1 --port 8020
```

Then: `GET /health`, `POST /sap-to-md/run` (JSON). MCP client: `http://127.0.0.1:8020/mcp`.

Standalone MCP:

```bash
md-sap-mcp --transport stdio
```

## Meta-router

```bash
mdengine sap-to-md ./sap-sources --output ./out
```

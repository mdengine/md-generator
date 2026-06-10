# odata-to-md

Convert OData CSDL metadata (V1–V4, XML + JSON) into AI-ready Markdown catalogs.

Works **standalone** via `md-odata`, or **inside SAP** via `md-sap` when OData files are part of a mixed SAP export.

## Install

```bash
pip install -e ".[odata]"
pip install -e ".[odata,api,mcp]"   # HTTP API + MCP
```

## CLI

```bash
md-odata generate --folder ./metadata-exports --output ./out
md-odata generate --file metadata.xml --output ./out
md-odata generate --url "https://host/sap/opu/odata/sap/API_PRODUCT/$metadata" --output ./out
md-odata generate --folder ./odata --output ./out --graph --chunk

mdengine odata-to-md generate --folder ./odata --output ./out
```

## API

```bash
md-odata-api
# GET /health
# POST /odata-to-md/generate — upload metadata XML/JSON → ZIP (port 8017)
```

## MCP

```bash
md-odata-mcp --transport stdio
```

## Dual mode

See [docs/dual-mode.md](docs/dual-mode.md) for when to use `md-odata` vs `md-sap`.

## Output

See [docs/output-layout.md](docs/output-layout.md).

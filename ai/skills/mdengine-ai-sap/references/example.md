# Examples — SAP → Markdown

## CLI (ABAP + CDS + DDIC)

```bash
pip install "mdengine[sap]"
md-sap ./sap-repo --output ./sap-md-out \
  --include-cds --include-ddic --graph --chunk \
  --pipeline-version 2 --workers 4
```

## CLI (HANA / mixed artifact tree)

Discovery picks up HANA, BW, and Datasphere files under the input tree automatically:

```bash
md-sap ./landscape-export --output ./out --include-lineage --include-governance
```

## CLI (OData $metadata URLs inside SAP run)

```bash
md-sap ./local-sources --odata-url "https://host/sap/opu/odata/sap/SERVICE/$metadata" --output ./out
```

For **OData-only** CSDL export, prefer `md-odata generate` (see [OData examples](../mdengine-ai-odata/references/example.md)).

## CLI (feature subset)

```bash
md-sap ./repo --output ./out --include entities,relationships,graphs --exclude governance
```

## CLI (async job)

```bash
md-sap ./large-repo --output ./out --async
```

## API + MCP

```bash
pip install "mdengine[sap,api,mcp]"
export SAP_TO_MD_PORT=8020
md-sap-api
```

Then: `GET /health`, `POST /sap-to-md/run` (JSON). MCP: `http://127.0.0.1:8020/mcp`.

```bash
md-sap-mcp --transport stdio
```

## Meta-router

```bash
mdengine sap-to-md ./sap-sources --output ./out --include-ddic --graph
```

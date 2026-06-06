# Examples — OData → Markdown

## CLI (local metadata file)

```bash
pip install "mdengine[odata]"
md-odata generate --file ./service/$metadata.xml --output ./odata-md-out
```

## CLI (fetch from URL)

```bash
md-odata generate --url "https://services.odata.org/V4/OData/OData.svc/" --output ./out --graph --chunk
```

## CLI (folder or ZIP)

```bash
md-odata generate --folder ./metadata-bundle --output ./out
md-odata generate --zip ./exports/metadata.zip --output ./out
```

With YAML config:

```bash
md-odata generate --config ./odata-to-md.yaml --output ./out
```

## API + MCP

```bash
pip install "mdengine[odata,api,mcp]"
export ODATA_TO_MD_PORT=8017
md-odata-api
```

Then: `GET /health`, `POST /odata-to-md/generate` (multipart metadata upload). MCP client: `http://127.0.0.1:8017/mcp`.

Standalone MCP:

```bash
md-odata-mcp --transport stdio
```

## Meta-router

```bash
mdengine odata-to-md generate --file ./$metadata.xml --output ./out
```

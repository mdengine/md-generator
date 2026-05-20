# sap-to-md

Convert SAP artifacts (ABAP, CDS, DDIC exports, OData, BAPI, IDoc, transport) into AI-ready Markdown knowledge packs.

## Install

```bash
pip install -e ".[sap,api]"
```

## CLI

```bash
md-sap ./sap-source --output ./out --graph --chunk
mdengine sap-to-md ./sap-source --include-governance --include-lineage
```

## API

```bash
md-sap-api
# POST /sap-to-md/run — sync ZIP export
# POST /sap-to-md/job — async job
```

See [docs/architecture.md](docs/architecture.md) for design details.

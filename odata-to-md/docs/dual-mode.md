# Dual mode: md-odata vs md-sap

## Use `md-odata` when

- Input is **only** OData `$metadata` (files, folder, ZIP, or URLs)
- You want a **lightweight** install (`pip install mdengine[odata]`)
- You need the dedicated **odata/** catalog without ABAP/CDS entity docs
- You want **HTTP API / MCP** at port 8017

```bash
md-odata generate --folder ./odata-exports --output ./out --graph --chunk
```

## Use `md-sap` when

- OData metadata lives **alongside** ABAP, CDS, DDIC, BAPI, IDoc, transport exports
- You need **mixed knowledge packs**: governance, lineage, authorization on SAP objects
- You want **entities/** 12-section docs for `ODATA_ENTITY` plus analyzers
- You need a **unified graph** linking CDS views, tables, programs, and OData nav

```bash
md-sap ./sap-source --output ./out --graph --chunk
md-sap --odata-url "https://.../$metadata" --output ./out
```

## OData-only via SAP CLI

Use [examples/odata-only-sap.yaml](../examples/odata-only-sap.yaml) to disable non-OData parsers while keeping SAP pipeline features (chunks, graph on SapObjects):

```bash
md-sap ./odata-metadata --config sap-to-md/examples/odata-only-sap.yaml --output ./out
```

## Shared core

Both paths use **`md_generator.odata`** for parsing (V1–V4), Capabilities, and the `odata/` catalog renderer. SAP adds `SapObject` emission and analyzer integration on top.

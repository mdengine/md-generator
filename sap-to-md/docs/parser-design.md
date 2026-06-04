# OData parser design

The shared OData core lives in **`md_generator.odata`**. The SAP module consumes it via thin re-export shims under `sap/parser/odata/`.

Standalone CLI: **`md-odata`** / **`mdengine odata-to-md`**. See [odata-to-md/docs/dual-mode.md](../../odata-to-md/docs/dual-mode.md).

## Version matrix

| Version | Format | Parser | Notes |
|---------|--------|--------|-------|
| 1.0 | EDMX XML | `parser/odata/xml/v1.py` | Best-effort; Association-based model |
| 2.0 | EDMX XML | `parser/odata/xml/v2_v3.py` | Production SAP Gateway path |
| 3.0 | EDMX XML | `parser/odata/xml/v2_v3.py` | FunctionImport / ActionImport |
| 4.0 | EDMX XML | `parser/odata/xml/v4.py` | Actions, functions, Capabilities |
| 4.0 | CSDL JSON | `parser/odata/json/v4.py` | `$EntityType`, `$EntityContainer` |

## Architecture

1. **detector.py** — format (XML vs JSON) and version sniffing (`md_generator.odata.parser`)
2. **namespaces.py** — namespace-agnostic XML helpers
3. **registry.py** — dispatches to version-specific parsers
4. **capabilities.py** — `Org.OData.Capabilities.V1` term parsing
5. **associations.py** — V2 association index and nav resolution
6. **legacy.py** — `to_legacy_entity_dict()` for backward-compatible `raw_metadata["odata"]`
7. **parser.py** — thin facade (`ODataParserPlugin`, `parse_odata_metadata`)

## Canonical model

All parsers emit `ODataMetadataDocument` with stable IDs (`odata:v2_0:SAP:entity:Customer`).

Catalog objects emitted as `SapObject` with `category=API`:

- `ODATA_SERVICE`, `ODATA_ENTITY_SET`, `ODATA_ENTITY`, `ODATA_ACTION`, `ODATA_FUNCTION`

Schema artifacts (ComplexType, EnumType, Singleton) stay in `odata_analysis` only.

## Discovery

`parser/discovery.py` recognizes:

- `metadata.xml`, `$metadata.xml`, `*.edmx`, `*metadata*.xml`
- `metadata.json`, `$metadata.json`, JSON with `@odata.context` or `$EntityType`

BAPI JSON is excluded via stricter `can_parse()` on the OData plugin.

## Backward compatibility

- `ODataParserPlugin.name == "odata"`
- `raw_metadata["odata"]` retains `name`, `properties`, `navigation` for entities
- Existing V2 fixture (`CUSTOMER`) unchanged

## URL fetch (optional)

Use `--odata-url` or `input.odata_urls[]`. Requires `httpx` (`pip install mdengine[sap]`).

Fetched documents populate `metadata_url` and inferred `service_root` on the canonical model.

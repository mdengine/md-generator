# OData catalog output

When the `odata_catalog` feature is enabled (default), the pipeline writes a dedicated tree under `odata/`.

## Layout

| Path | Content |
|------|---------|
| `odata/index.md` | Service catalog, entity-set index, action/function index, version summary — RAG bootstrap |
| `odata/services/{service}.md` | Service overview, version, namespace, container, metadata URL, service root |
| `odata/entity-sets/{service}_{set}.md` | Entity type, CRUD from Capabilities, supported query options |
| `odata/entity-types/{service}_{type}.md` | Properties, keys, navigation properties |
| `odata/actions/{service}_{action}.md` | Bound/unbound actions |
| `odata/functions/{service}_{function}.md` | Functions and return types |

Legacy `entities/` output for `ODATA_ENTITY` objects is unchanged for backward compatibility.

## Query options

Entity-set pages include **Supported Query Options** derived from:

1. `Org.OData.Capabilities.V1` annotations (primary)
2. OData version defaults when Capabilities are absent

Options include `$filter`, `$select`, `$expand`, `$orderby`, `$search`, `$top`, `$skip`, `$count`.

## Stable IDs

Graph nodes, chunks, and catalog metadata use stable IDs:

```
odata:v2_0:SAP:entity:Customer
odata:v4_0:com.example:entitySet:Products
```

These map to `SapObject.object_id` via `raw_metadata["stable_id"]`.

## Chunk types

When chunking is enabled, OData-specific strategies produce:

- `odata_service` — service catalog entry
- `odata_entity_set` — entity-set page with capabilities
- `odata_capabilities` — CRUD/query restrictions summary
- `odata_index` — bootstrap from catalog index

## Configuration

```yaml
features:
  include:
    - odata_catalog

input:
  odata_urls:
    - https://example.com/sap/opu/odata/sap/API_PRODUCT/$metadata

odata:
  fetch_timeout_sec: 30
  verify_tls: true
  cache_fetched: true
```

CLI: `md-sap --odata-url https://...`

# ADT DDIC XML exports

This project parses SAP ABAP Development Tools (ADT) dictionary XML exports (`wbobj/dictionary/*`).

## Supported ADT object types

| ADT type | Kind | Fixture example |
|----------|------|-----------------|
| `DTEL/DE` | Data element | `char100.dtel.xml` |
| `DOMA/DD` | Domain | `char100.dom.xml` |
| `TABL/DS` | Structure | `bal_s_cont.tabl.xml` |
| `TABL/DT` | Table | `t005.tabl.xml` |
| `TTYP/DA` | Table type | `bal_t_cont.ttyp.xml` |
| `RSDT/RS` | Range type | `char100_range.rsdt.xml` |
| `REFT/RT` | Reference type | `char100_ref.reft.xml` |

## Exporting from SAP

From Eclipse ADT, export dictionary objects as XML, or use CLI tools:

```bash
erpl-adt ddic table SFLIGHT --raw
erpl-adt ddic table T005 --raw
```

## Modern TABL/DT (DDL source)

On ABAP Platform 7.5+ / ABAP Cloud, transparent tables (`TABL/DT`) may return a `blueSource` payload with a link to DDL source instead of inline `field` elements. The parser accepts this gracefully with `definition_source: adt_xml_ddl_ref` and empty fields.

For full field lists on modern systems, use:

- CDS `define table` DDL exports (`.ddls`), or
- ADT DDL source endpoint `/sap/bc/adt/ddic/tables/{name}/source/main`

## Output layout

Structures from ADT (`STRUCTURE`) and CDS (`define type`) both render to **`structures/{name}.md`**.

Other DDIC kinds render under `ddic/data-elements/`, `ddic/domains/`, `ddic/tables/`, etc.

## Canonical metadata (`ddic_canonical`)

Normalized DDIC artifacts include a typed **`ddic_canonical`** block alongside legacy keys (`data_element`, `domain`, `structure`, `ddic`, etc.).

```json
{
  "object_kind": "DATA_ELEMENT",
  "definition_source": "adt_xml",
  "payload": {
    "kind": "DATA_ELEMENT",
    "type_kind": "domain",
    "type_name": "CHAR100",
    "data_type": "CHAR",
    "data_type_length": 100,
    "data_type_decimals": 0
  }
}
```

The `payload` field is a **discriminated union** (`DataElementMetadata`, `StructureMetadata`, `TableMetadata`, …) keyed by `kind`.

v2 markdown generators resolve views via `object_kind` using `ddic_canonical_io.resolve_ddic_meta()`. Legacy keys remain for one release for v1 entity docs and external tooling; prefer `ddic_canonical` for new integrations.

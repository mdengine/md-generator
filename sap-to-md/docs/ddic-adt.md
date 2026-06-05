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

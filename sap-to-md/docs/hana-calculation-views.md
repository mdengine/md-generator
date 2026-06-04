# HANA Calculation Views

## Input

SAP HANA `Calculation:scenario` XML (`.xml`, `.calculationview`).

## Parser

`parser/hana/calculation_view.py` uses `lxml.iterparse` for streaming parse of large exports.

Emits:

- **CalculationView** canonical model (no embedded lineage graph)
- **TransformationGraph** (join, projection, source nodes)
- **ArtifactGraph** fragments (`READS_FROM`, `JOINS`, `DERIVES_FROM`)

## Pipeline v2 outputs

```
hana/calculation-views/{slug}.md
hana/diagrams/{slug}.mmd
hana/sql/{slug}.sql
hana/lineage/{slug}.json
hana/impact/{slug}.md
json/canonical/{safe_stable_id}.json
```

## CLI

```bash
md-sap --pipeline-version 2 ./fixtures/hana --output ./out
```

## Fixture

See `sap-to-md/tests/fixtures/hana/cv_sales.xml`.

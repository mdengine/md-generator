# SAP Intelligence Responsibilities

## In scope

- networkx
- pyyaml
- pydantic
- httpx
- lxml
- governance module
- optional tree-sitter ABAP
- CrossLinkRegistry
- UnifiedOutputRegistry

- Expose `md-sap` CLI for local and CI usage.
- Convert ABAP, CDS/DDL, DDIC (ADT XML, abapGit `.tabl.xml`), HANA CV exports, BW, Datasphere, OData $metadata, BAPI, IDoc, transport files to Canonical JSON, per-artifact Markdown (DDIC/HANA/CDS/ABAP), lineage/impact graphs, semantic narrative, cross-linked knowledge packs, optional chunks.
- Provide FastAPI + optional MCP integration.

## Supported artifact types (generators)

`hana.calculation_view`, `hana.analytic_view`, `hana.attribute_view`, `hana.hdi_calculation_view`, `hana.sql_view`, `cds.view`, `cds.structure`, `ddic.table`, `ddic.data_element`, `ddic.domain`, `ddic.structure`, `ddic.table_type`, `ddic.range_type`, `ddic.reference_type`, `abap.program`, `odata.entity`, `bw.adso`, `bw.composite_provider`, `bw.transformation`, `bw.dtp` (+4 more)

Parsers are toggled independently via `parser.include_abap`, `include_cds`, `include_ddic`, `include_hana`, `include_bw`, `include_datasphere`, `include_external`, plus YAML `parser.plugins`.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.

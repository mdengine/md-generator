# `md_generator.sap` API Reference

## Summary

| Item | Value |
|------|-------|
| Purpose | Convert ABAP, CDS/DDL, DDIC (ADT XML, abapGit `.tabl.xml`), HANA CV exports, BW, Datasphere, OData $metadata, BAPI, IDoc, transport files to Canonical JSON, per-artifact Markdown (DDIC/HANA/CDS/ABAP), lineage/impact graphs, semantic narrative, cross-linked knowledge packs, optional chunks |
| CLI | `md-sap` |
| Extra | `sap` |
| Tier | `complex` |

## Quick CLI reference

| Argument | Type | Required | Default | Choices | Help |
| --- | --- | --- | --- | --- | --- |
| `input` | Path | required | — | — | SAP source paths (files or directories) |
| `--config` | Path | optional | None | — | Path to YAML config |
| `--output` | Path | optional | None | — | Output directory |
| `--include` | str | optional | None | — | Comma-separated feature list |
| `--exclude` | str | optional | None | — | — |
| `--include-cds` | flag | optional | false | — | Enable CDS parser |
| `--include-ddic` | flag | optional | false | — | Enable DDIC parser |
| `--include-lineage` | flag | optional | false | — | Enable lineage analyzer |
| `--include-governance` | flag | optional | false | — | Enable governance analyzer |
| `--graph` | flag | optional | false | — | Export relationship graphs |
| `--chunk` | flag | optional | false | — | Write semantic chunks |
| `--json-output` | flag | optional | false | — | Include json_output feature |
| `--odata-url` | str | optional | [] | — | Fetch OData $metadata from URL (repeatable) |
| `--async` | flag | optional | false | — | Run as background job |
| `--pipeline-version` | int | optional | None | — | Pipeline version (1=legacy, 2=canonical+graph) |


## Primary symbols

| Symbol | Kind | Notes |
| --- | --- | --- |
| extract_to_markdown | callable | — |
| SapRunConfig | callable | — |
| load_run_config | callable | — |
| SapJobManager | callable | — |
| format_semantic_narrative | callable | — |


## Python API (mkdocstrings)

::: md_generator.sap
    options:
      show_source: false
      show_root_heading: true
      show_signature_annotations: true
      members_order: source
      filters:
        - "!^_"

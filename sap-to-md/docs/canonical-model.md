# Canonical model

The v2 pipeline emits typed **CanonicalArtifact** JSON under `json/canonical/`.

## ArtifactIdentity

Multi-layer identity supports cross-system lineage:

| Field | Purpose |
|-------|---------|
| `stable_id` | Immutable graph node key |
| `physical_id` | Deployed object name (HANA FQN, table name) |
| `semantic_id` | Business entity (e.g. `entity:sales_order`) |
| `runtime_id` | OData URI / BW runtime path |
| `display_id` | Human label |
| `namespace` | `HANA::`, `CDS::`, `ODATA::`, `DDIC::`, `ABAP::` |

## ProvenanceBundle

Every canonical JSON includes parser/schema versions, run id, checksum, and `parsed_at` for reproducibility.

## TransformationGraph

Universal DAG (`TransformationNode` specializations) models HANA joins/projections, BW flows, and Datasphere pipelines without embedding lineage inside artifact-specific blobs.

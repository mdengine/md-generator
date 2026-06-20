# SAP Intelligence Use Cases

### Local developer conversion

| Aspect | Detail |
|--------|--------|
| Objective | Convert a single ABAP, CDS/DDL, DDIC (ADT XML, abapGit `.tabl.xml`), HANA CV exports, BW, Datasphere, OData $metadata, BAPI, IDoc, transport files during feature work. |
| Input | Sample ABAP, CDS/DDL, DDIC (ADT XML, abapGit `.tabl.xml`), HANA CV exports, BW, Datasphere, OData $metadata, BAPI, IDoc, transport files |
| Output | Canonical JSON, per-artifact Markdown (DDIC/HANA/CDS/ABAP), lineage/impact graphs, semantic narrative, cross-linked knowledge packs, optional chunks |
| Configuration | `pip install -e ".[sap]"` |
| Performance | Fast for small inputs; use job API for large bundles. |
| Failure | Missing extra, invalid input, timeout, upload too large |
| Recovery | Fix input; retry with job endpoint; increase limits via env |

### CI documentation artifact

| Aspect | Detail |
|--------|--------|
| Objective | Publish Markdown into build artifacts for review. |
| Input | Tracked input files |
| Output | Artifact directory or ZIP |
| Configuration | CLI in pipeline + cache extras |
| Performance | Pin extras in CI image; cache Whisper/browser deps separately for media modules. |
| Failure | Missing extra, invalid input, timeout, upload too large |
| Recovery | Fix input; retry with job endpoint; increase limits via env |

### Gateway HTTP service

| Aspect | Detail |
|--------|--------|
| Objective | Expose conversion behind nginx path prefix. |
| Input | Multipart upload or JSON body |
| Output | ZIP or JSON status |
| Configuration | `api` extra + Docker |
| Performance | Set upload limits and timeouts at gateway. |
| Failure | Missing extra, invalid input, timeout, upload too large |
| Recovery | Fix input; retry with job endpoint; increase limits via env |

### Batch directory processing

| Aspect | Detail |
|--------|--------|
| Objective | Process many files overnight. |
| Input | Directory tree |
| Output | Per-file output folders |
| Configuration | Shell loop or job endpoints |
| Performance | Disk space and temp job TTL matter. |
| Failure | Missing extra, invalid input, timeout, upload too large |
| Recovery | Fix input; retry with job endpoint; increase limits via env |

### AI/RAG ingestion

| Aspect | Detail |
|--------|--------|
| Objective | Feed Markdown into embeddings index. |
| Input | Canonical JSON, per-artifact Markdown (DDIC/HANA/CDS/ABAP), lineage/impact graphs, semantic narrative, cross-linked knowledge packs, optional chunks |
| Output | Chunked Markdown |
| Configuration | Stable naming + front matter if enabled |
| Performance | Sanitize secrets before indexing. |
| Failure | Missing extra, invalid input, timeout, upload too large |
| Recovery | Fix input; retry with job endpoint; increase limits via env |

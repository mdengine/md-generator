# OpenAPI Use Cases

### Local developer conversion

| Aspect | Detail |
|--------|--------|
| Objective | Convert a single OpenAPI 3.x or Swagger 2.0 during feature work. |
| Input | Sample OpenAPI 3.x or Swagger 2.0 |
| Output | API documentation ZIP bundle |
| Configuration | `pip install -e ".[openapi]"` |
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
| Input | API documentation ZIP bundle |
| Output | Chunked Markdown |
| Configuration | Stable naming + front matter if enabled |
| Performance | Sanitize secrets before indexing. |
| Failure | Missing extra, invalid input, timeout, upload too large |
| Recovery | Fix input; retry with job endpoint; increase limits via env |

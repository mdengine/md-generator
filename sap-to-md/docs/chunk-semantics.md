# Chunk semantics (SemanticChunkSpec)

Pipeline v2 can emit RAG-ready chunks as JSONL (`chunks/semantic.jsonl`).

```yaml
pipeline:
  semantic_chunks_jsonl: true
```

Each **SemanticChunkSpec** includes:

| Field | Purpose |
|-------|---------|
| `chunk_type` | e.g. `join_analysis`, `lineage_summary`, `optimization` |
| `semantic_tags` | `lineage`, `performance`, `governance` |
| `graph_refs` | Edge IDs the chunk describes |
| `embedding_hint` | Optional hint for vectorization |

Legacy v1 chunk strategies remain unchanged when `pipeline.version: 1`.

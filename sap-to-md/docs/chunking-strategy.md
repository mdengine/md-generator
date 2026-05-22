# Chunking strategy

Reuses `SemanticChunk` and `MarkdownArtifact` from the shared core.

Chunk types: `entity`, `relationship`, `validation`, `authorization`, `lineage`.

Output: `chunks/*.md` with YAML frontmatter, `chunks/index.json`, `chunks.jsonl`.

Enable via `--chunk` or `chunking.enabled: true` in YAML.

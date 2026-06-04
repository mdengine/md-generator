# Output layout

Standalone `md-odata generate` writes:

| Path | Content |
|------|---------|
| `odata/index.md` | Service catalog bootstrap |
| `odata/services/` | Per-service overview |
| `odata/entity-sets/` | CRUD + query options |
| `odata/entity-types/` | Properties and navigation |
| `odata/actions/`, `odata/functions/` | Operations |
| `json/` | Canonical document JSON (when enabled) |
| `graph-full.json` | With `--graph` |
| `graphs/relationships.mmd` | With `--graph` |
| `chunks/` | With `--chunk` |
| `export_manifest.json` | Run summary |

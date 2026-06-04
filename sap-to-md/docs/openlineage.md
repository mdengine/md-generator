# OpenLineage export

`graph/adapters/openlineage.py` maps internal graphs to OpenLineage-style JSON.

Enable export:

```yaml
pipeline:
  version: 2
  openlineage_export: true
```

Output: `lineage/openlineage.json`

| Internal | OpenLineage |
|----------|-------------|
| GraphNode (dataset) | Dataset |
| Parser run | Run + Job |
| TRANSFORMS edge | InputDataset → OutputDataset |
| Column mapping | ColumnLineage facet |

Cross-system `SAME_AS` edges are linked in Phase 5 via `SemanticEntityRegistry`.

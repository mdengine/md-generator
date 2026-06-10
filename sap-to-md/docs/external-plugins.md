# External plugins

Enable non-SAP parsers:

```yaml
parser:
  include_external: true
```

Supported: dbt `manifest.json`, Snowflake DDL `.sql`, Kafka `.avsc`, Informatica mapping XML.

Cross-system lineage uses confidence-scored `SAME_AS` edges.

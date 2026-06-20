# Database Metadata Configuration

Configuration surfaces:

1. **CLI flags** — `md-db --help`
2. **Environment variables** — see `parameters.md`
3. **Run config dataclasses** — `src/md_generator/db/**/run_config.py`
4. **YAML presets** — `src\md_generator\db\config\default.yaml`

## YAML keys (extracted defaults)

| Config file | Key | Default / sample |
| --- | --- | --- |
| src\md_generator\db\config\default.yaml | database.type | 'postgres' |
| src\md_generator\db\config\default.yaml | database.uri | 'postgresql://user:pass@localhost:5432/dbname' |
| src\md_generator\db\config\default.yaml | database.schema | 'public' |
| src\md_generator\db\config\default.yaml | output.path | './docs' |
| src\md_generator\db\config\default.yaml | output.split_files | True |
| src\md_generator\db\config\default.yaml | output.write_combined_feature_markdown | False |
| src\md_generator\db\config\default.yaml | output.readme_feature_merge | 'none' |
| src\md_generator\db\config\default.yaml | features.include | 'tables', 'views', 'indexes', 'procedures', ... |
| src\md_generator\db\config\default.yaml | features.exclude | [] |
| src\md_generator\db\config\default.yaml | execution.workers | 4 |
| src\md_generator\db\config\default.yaml | limits.max_tables | 10000 |
| src\md_generator\db\config\default.yaml | limits.max_collections | 500 |
| src\md_generator\db\config\default.yaml | limits.sample_size | 50 |
| src\md_generator\db\config\default.yaml | erd.max_tables | 100 |
| src\md_generator\db\config\default.yaml | erd.scope | 'full' |


## Example

```bash
md-db --help
```

For HTTP services, configure upload limits and CORS via module `settings.py` environment variables.

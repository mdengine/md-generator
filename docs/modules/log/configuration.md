# Log Analysis Configuration

Configuration surfaces:

1. **CLI flags** — `md-log --help`
2. **Environment variables** — see `parameters.md`
3. **Run config dataclasses** — `src/md_generator/log/**/run_config.py`
4. **YAML presets** — `src\md_generator\log\config\default.yaml`, `src\md_generator\log\config\presets\generic.yaml`, `src\md_generator\log\config\presets\json.yaml`, `src\md_generator\log\config\presets\logback.yaml`, `src\md_generator\log\config\presets\springboot.yaml`

## YAML keys (extracted defaults)

| Config file | Key | Default / sample |
| --- | --- | --- |
| src\md_generator\log\config\default.yaml | input.paths | [] |
| src\md_generator\log\config\default.yaml | input.otel_path | null |
| src\md_generator\log\config\default.yaml | parser.preset | 'generic' |
| src\md_generator\log\config\default.yaml | parser.fuzzy_timestamp | False |
| src\md_generator\log\config\default.yaml | parser.auto_detect | False |
| src\md_generator\log\config\default.yaml | parser.preset_dirs | [] |
| src\md_generator\log\config\default.yaml | normalization.redact_pii | False |
| src\md_generator\log\config\default.yaml | normalization.normalize_numbers | False |
| src\md_generator\log\config\default.yaml | normalization.normalize_uuid | False |
| src\md_generator\log\config\default.yaml | normalization.normalize_paths | False |
| src\md_generator\log\config\default.yaml | aggregation.timeline | 'hourly' |
| src\md_generator\log\config\default.yaml | clustering.enabled | False |
| src\md_generator\log\config\default.yaml | clustering.algorithm | 'kmeans' |
| src\md_generator\log\config\default.yaml | clustering.n_clusters | 8 |
| src\md_generator\log\config\default.yaml | clustering.random_state | 42 |
| src\md_generator\log\config\default.yaml | clustering.max_features | 4096 |
| src\md_generator\log\config\default.yaml | output.path | './log-docs' |
| src\md_generator\log\config\default.yaml | output.split_by_level | True |
| src\md_generator\log\config\default.yaml | output.generate_incidents | True |
| src\md_generator\log\config\default.yaml | output.generate_clusters | False |
| src\md_generator\log\config\default.yaml | output.generate_chunks | False |
| src\md_generator\log\config\default.yaml | output.frontmatter | False |
| src\md_generator\log\config\default.yaml | chunk.enabled | False |
| src\md_generator\log\config\default.yaml | chunk.lines_per_chunk | 100000 |
| src\md_generator\log\config\default.yaml | chunk.records_per_md_chunk | 500 |
| src\md_generator\log\config\default.yaml | execution.workers | 4 |
| src\md_generator\log\config\default.yaml | execution.max_lines_per_file | null |
| src\md_generator\log\config\default.yaml | execution.encoding_fallbacks | 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252' |
| src\md_generator\log\config\default.yaml | execution.batch_records | 10000 |
| src\md_generator\log\config\default.yaml | execution.use_runtime | False |
| src\md_generator\log\config\default.yaml | execution.distributed | False |
| src\md_generator\log\config\default.yaml | plugins.enrichers | [] |
| src\md_generator\log\config\default.yaml | incidents.min_occurrences | 2 |
| src\md_generator\log\config\default.yaml | incidents.levels | 'ERROR', 'FATAL', 'WARN' |
| src\md_generator\log\config\default.yaml | incidents.stacktrace_aware | True |


## Example

```bash
md-log --help
```

For HTTP services, configure upload limits and CORS via module `settings.py` environment variables.

# SAP Intelligence Configuration

Configuration surfaces:

1. **CLI flags** — `md-sap --help`
2. **Environment variables** — see `parameters.md`
3. **Run config dataclasses** — `src/md_generator/sap/**/run_config.py`
4. **YAML presets** — `src\md_generator\sap\config\default.yaml`

## YAML keys (extracted defaults)

| Config file | Key | Default / sample |
| --- | --- | --- |
| src\md_generator\sap\config\default.yaml | input.paths | [] |
| src\md_generator\sap\config\default.yaml | input.odata_urls | [] |
| src\md_generator\sap\config\default.yaml | output.path | 'output/sap-md' |
| src\md_generator\sap\config\default.yaml | output.split_files | True |
| src\md_generator\sap\config\default.yaml | output.write_manifest | True |
| src\md_generator\sap\config\default.yaml | output.markdown_cross_links | True |
| src\md_generator\sap\config\default.yaml | features.include | 'entities', 'technical', 'functional', 'relationships', ... |
| src\md_generator\sap\config\default.yaml | features.exclude | [] |
| src\md_generator\sap\config\default.yaml | parser.plugins | [] |
| src\md_generator\sap\config\default.yaml | parser.include_abap | True |
| src\md_generator\sap\config\default.yaml | parser.include_cds | True |
| src\md_generator\sap\config\default.yaml | parser.include_ddic | True |
| src\md_generator\sap\config\default.yaml | parser.include_odata | True |
| src\md_generator\sap\config\default.yaml | parser.include_bapi | True |
| src\md_generator\sap\config\default.yaml | parser.include_idoc | True |
| src\md_generator\sap\config\default.yaml | parser.include_transport | True |
| src\md_generator\sap\config\default.yaml | parser.include_hana | True |
| src\md_generator\sap\config\default.yaml | parser.include_bw | True |
| src\md_generator\sap\config\default.yaml | parser.include_datasphere | True |
| src\md_generator\sap\config\default.yaml | parser.include_external | False |
| src\md_generator\sap\config\default.yaml | odata.fetch_timeout_sec | 30 |
| src\md_generator\sap\config\default.yaml | odata.verify_tls | True |
| src\md_generator\sap\config\default.yaml | odata.cache_fetched | True |
| src\md_generator\sap\config\default.yaml | analyzer.lineage | True |
| src\md_generator\sap\config\default.yaml | analyzer.governance | True |
| src\md_generator\sap\config\default.yaml | analyzer.relationships | True |
| src\md_generator\sap\config\default.yaml | analyzer.validations | True |
| src\md_generator\sap\config\default.yaml | analyzer.authorization | True |
| src\md_generator\sap\config\default.yaml | analyzer.semantics | True |
| src\md_generator\sap\config\default.yaml | chunking.enabled | False |
| src\md_generator\sap\config\default.yaml | chunking.types | 'entity', 'relationship', 'validation', 'authorization', ... |
| src\md_generator\sap\config\default.yaml | graph.enabled | False |
| src\md_generator\sap\config\default.yaml | graph.mermaid | True |
| src\md_generator\sap\config\default.yaml | graph.json_export | True |
| src\md_generator\sap\config\default.yaml | performance.workers | 4 |


## Example

```bash
md-sap --help
```

For HTTP services, configure upload limits and CORS via module `settings.py` environment variables.

# SAP Intelligence Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `input` | Path | required | — | — | SAP source paths (files or directories) |
| `--config` | Path | optional | None | — | Path to YAML config |
| `--output` | Path | optional | None | — | Output directory |
| `--include` | str | optional | None | — | Comma-separated feature list |
| `--exclude` | str | optional | None | — | — |
| `--include-cds` | flag | optional | false | — | Enable CDS parser |
| `--include-ddic` | flag | optional | false | — | Enable DDIC parser |
| `--include-lineage` | flag | optional | false | — | Enable lineage analyzer |
| `--include-governance` | flag | optional | false | — | Enable governance analyzer |
| `--graph` | flag | optional | false | — | Export relationship graphs |
| `--chunk` | flag | optional | false | — | Write semantic chunks |
| `--json-output` | flag | optional | false | — | Include json_output feature |
| `--odata-url` | str | optional | [] | — | Fetch OData $metadata from URL (repeatable) |
| `--async` | flag | optional | false | — | Run as background job |
| `--pipeline-version` | int | optional | None | — | Pipeline version (1=legacy, 2=canonical+graph) |
| `--workers` | int | optional | None | — | Parallel parser workers |


## API routes (HTTP parameters)

| Method | Path | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| GET | /health | HTTP | — | — | FastAPI route |
| POST | /sap-to-md/run | HTTP | — | — | FastAPI route |
| POST | /sap-to-md/job | HTTP | — | — | FastAPI route |
| GET | /sap-to-md/job/{job_id} | HTTP | — | — | FastAPI route |
| GET | /sap-to-md/job/{job_id}/download | HTTP | — | — | FastAPI route |


## Environment variables

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| SAP_TO_MD_PORT | string/int | optional | varies | — | HTTP API listen port |


## Config files

| File | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| src\md_generator\sap\config\default.yaml | YAML | optional | — | — | Packaged or preset config |


## YAML config keys (from packaged defaults)

| File | Key | Default / sample | Required | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| src\md_generator\sap\config\default.yaml | input.paths | [] | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | input.odata_urls | [] | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | output.path | 'output/sap-md' | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | output.split_files | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | output.write_manifest | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | output.markdown_cross_links | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | features.include | 'entities', 'technical', 'functional', 'relationships', ... | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | features.exclude | [] | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | parser.plugins | [] | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | parser.include_abap | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | parser.include_cds | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | parser.include_ddic | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | parser.include_odata | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | parser.include_bapi | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | parser.include_idoc | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | parser.include_transport | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | parser.include_hana | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | parser.include_bw | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | parser.include_datasphere | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | parser.include_external | False | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | odata.fetch_timeout_sec | 30 | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | odata.verify_tls | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | odata.cache_fetched | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | analyzer.lineage | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | analyzer.governance | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | analyzer.relationships | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | analyzer.validations | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | analyzer.authorization | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | analyzer.semantics | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | chunking.enabled | False | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | chunking.types | 'entity', 'relationship', 'validation', 'authorization', ... | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | graph.enabled | False | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | graph.mermaid | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | graph.json_export | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | performance.workers | 4 | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | performance.cache_dir | null | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | performance.incremental | True | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | performance.stream_threshold_mb | 5 | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | performance.intelligence_list_cap | 80 | optional | — | From packaged YAML |
| src\md_generator\sap\config\default.yaml | pipeline.version | 1 | optional | — | From packaged YAML |


## Run config dataclass fields

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| PipelineSection | version | int | varies | 1 | Run config dataclass field |
| PipelineSection | canonical_json | bool | varies | True | Run config dataclass field |
| PipelineSection | artifact_graph | bool | varies | True | Run config dataclass field |
| PipelineSection | rule_engine | bool | varies | True | Run config dataclass field |
| PipelineSection | openlineage_export | bool | varies | False | Run config dataclass field |
| PipelineSection | cross_lineage | bool | varies | False | Run config dataclass field |
| PipelineSection | semantic_chunks_jsonl | bool | varies | False | Run config dataclass field |
| PipelineSection | semantic_narrative | bool | varies | False | Run config dataclass field |
| ParserSection | plugins | list[str] | varies | field(default_factory=list) | Run config dataclass field |
| ParserSection | include_abap | bool | varies | True | Run config dataclass field |
| ParserSection | include_cds | bool | varies | True | Run config dataclass field |
| ParserSection | include_ddic | bool | varies | True | Run config dataclass field |
| ParserSection | include_odata | bool | varies | True | Run config dataclass field |
| ParserSection | include_bapi | bool | varies | True | Run config dataclass field |
| ParserSection | include_idoc | bool | varies | True | Run config dataclass field |
| ParserSection | include_transport | bool | varies | True | Run config dataclass field |
| ParserSection | include_hana | bool | varies | True | Run config dataclass field |
| ParserSection | include_bw | bool | varies | True | Run config dataclass field |
| ParserSection | include_datasphere | bool | varies | True | Run config dataclass field |
| ParserSection | include_external | bool | varies | False | Run config dataclass field |
| AnalyzerSection | lineage | bool | varies | True | Run config dataclass field |
| AnalyzerSection | governance | bool | varies | True | Run config dataclass field |
| AnalyzerSection | relationships | bool | varies | True | Run config dataclass field |
| AnalyzerSection | validations | bool | varies | True | Run config dataclass field |
| AnalyzerSection | authorization | bool | varies | True | Run config dataclass field |
| AnalyzerSection | semantics | bool | varies | True | Run config dataclass field |
| ChunkingSection | enabled | bool | varies | False | Run config dataclass field |
| ChunkingSection | types | list[str] | varies | field(default_factory=lambda: ['entity', 'rel... | Run config dataclass field |
| GraphSection | enabled | bool | varies | False | Run config dataclass field |
| GraphSection | mermaid | bool | varies | True | Run config dataclass field |
| GraphSection | json_export | bool | varies | True | Run config dataclass field |
| PerformanceSection | workers | int | varies | 4 | Run config dataclass field |
| PerformanceSection | cache_dir | str \| None | varies | None | Run config dataclass field |
| PerformanceSection | incremental | bool | varies | True | Run config dataclass field |
| PerformanceSection | stream_threshold_mb | int | varies | 5 | Run config dataclass field |
| PerformanceSection | intelligence_list_cap | int | varies | 80 | Run config dataclass field |
| ODataSection | fetch_timeout_sec | int | varies | 30 | Run config dataclass field |
| ODataSection | verify_tls | bool | varies | True | Run config dataclass field |
| ODataSection | cache_fetched | bool | varies | True | Run config dataclass field |
| SapRunConfig | input_paths | list[Path] | varies | field(default_factory=list) | Run config dataclass field |
| SapRunConfig | odata_urls | list[str] | varies | field(default_factory=list) | Run config dataclass field |
| SapRunConfig | output_path | Path | varies | field(default_factory=lambda: Path('output/sa... | Run config dataclass field |
| SapRunConfig | split_files | bool | varies | True | Run config dataclass field |
| SapRunConfig | include | frozenset[str] | varies | field(default_factory=lambda: frozenset(FEATU... | Run config dataclass field |
| SapRunConfig | exclude | frozenset[str] | varies | field(default_factory=frozenset) | Run config dataclass field |
| SapRunConfig | parser | ParserSection | varies | field(default_factory=ParserSection) | Run config dataclass field |
| SapRunConfig | odata | ODataSection | varies | field(default_factory=ODataSection) | Run config dataclass field |
| SapRunConfig | analyzer | AnalyzerSection | varies | field(default_factory=AnalyzerSection) | Run config dataclass field |
| SapRunConfig | chunking | ChunkingSection | varies | field(default_factory=ChunkingSection) | Run config dataclass field |
| SapRunConfig | graph | GraphSection | varies | field(default_factory=GraphSection) | Run config dataclass field |
| SapRunConfig | pipeline | PipelineSection | varies | field(default_factory=PipelineSection) | Run config dataclass field |
| SapRunConfig | performance | PerformanceSection | varies | field(default_factory=PerformanceSection) | Run config dataclass field |
| SapRunConfig | write_manifest | bool | varies | True | Run config dataclass field |
| SapRunConfig | markdown_cross_links | bool | varies | True | Run config dataclass field |


## Options / dataclass fields (sample)

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| InputSection | paths | list[str] | varies | — | Field on options/config class |
| OutputSection | path | str | varies | — | Field on options/config class |
| OutputSection | split_files | bool | varies | — | Field on options/config class |
| OutputSection | write_manifest | bool | varies | — | Field on options/config class |
| OutputSection | markdown_cross_links | bool | varies | — | Field on options/config class |
| FeaturesSection | include | list[str] \| None | varies | — | Field on options/config class |
| FeaturesSection | exclude | list[str] | varies | — | Field on options/config class |


## Registered types (generators / plugins)

| Artifact / plugin type | Registered in |
| --- | --- |
| hana.calculation_view | `src\md_generator\sap\generators\registry.py` |
| hana.analytic_view | `src\md_generator\sap\generators\registry.py` |
| hana.attribute_view | `src\md_generator\sap\generators\registry.py` |
| hana.hdi_calculation_view | `src\md_generator\sap\generators\registry.py` |
| hana.sql_view | `src\md_generator\sap\generators\registry.py` |
| cds.view | `src\md_generator\sap\generators\registry.py` |
| cds.structure | `src\md_generator\sap\generators\registry.py` |
| ddic.table | `src\md_generator\sap\generators\registry.py` |
| ddic.data_element | `src\md_generator\sap\generators\registry.py` |
| ddic.domain | `src\md_generator\sap\generators\registry.py` |
| ddic.structure | `src\md_generator\sap\generators\registry.py` |
| ddic.table_type | `src\md_generator\sap\generators\registry.py` |
| ddic.range_type | `src\md_generator\sap\generators\registry.py` |
| ddic.reference_type | `src\md_generator\sap\generators\registry.py` |
| abap.program | `src\md_generator\sap\generators\registry.py` |
| odata.entity | `src\md_generator\sap\generators\registry.py` |
| bw.adso | `src\md_generator\sap\generators\registry.py` |
| bw.composite_provider | `src\md_generator\sap\generators\registry.py` |
| bw.transformation | `src\md_generator\sap\generators\registry.py` |
| bw.dtp | `src\md_generator\sap\generators\registry.py` |
| bw.info_object | `src\md_generator\sap\generators\registry.py` |
| datasphere.analytical_model | `src\md_generator\sap\generators\registry.py` |
| datasphere.view | `src\md_generator\sap\generators\registry.py` |
| datasphere.data_flow | `src\md_generator\sap\generators\registry.py` |


## Feature flags

`authorization`, `chunks`, `entities`, `functional`, `governance`, `graphs`, `json_output`, `lineage`, `odata_catalog`, `relationships`, `technical`, `validations`

## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `sap`.

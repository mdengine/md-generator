# SAP Intelligence Extension Points

Parser plugins via YAML `parser.plugins`; parsers toggled with `parser.include_*`; generators in `sap/generators/registry.py`; pipeline v2 via `pipeline.version: 2` or `--pipeline-version 2`; semantic narrative via `pipeline.semantic_narrative`.

## Registered artifact / plugin types (from source)

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


## Safe extension patterns

- Add adapter implementations and register in factory modules.
- Add optional extras in `pyproject.toml` for heavy dependencies.
- Keep CLI/API thin — delegate to core functions for testability.

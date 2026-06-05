from __future__ import annotations

from md_generator.sap.analyzer.semantics.entity_mapper import infer_semantic_entity
from md_generator.sap.models.metadata.ddic import DdicTable
from md_generator.sap.parser.ddic.ddl_table_parser import is_ddl_table_source, parse_ddl_table


def is_cds_table_ddl(source: str) -> bool:
    return is_ddl_table_source(source)


def parse_cds_table_ddl(source: str, fallback_name: str) -> DdicTable:
    tbl = parse_ddl_table(source, fallback_name, definition_source="cds_ddl")
    for fld in tbl.fields:
        fld.business_name = infer_semantic_entity(fld.name, None)
    return tbl

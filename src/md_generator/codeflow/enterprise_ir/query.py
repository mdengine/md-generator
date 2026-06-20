from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from md_generator.codeflow.enterprise_ir.base import BaseEntity

QueryOperation = Literal[
    "READ",
    "WRITE",
    "UPDATE",
    "DELETE",
    "UPSERT",
    "DDL",
    "PROCEDURE",
    "FUNCTION",
    "PIPELINE",
]

QueryDialect = Literal[
    "ANSI",
    "Oracle",
    "Postgres",
    "MySQL",
    "SQL Server",
    "Mongo",
    "Redis",
    "Elastic",
    "Cypher",
    "CQL",
    "Unknown",
]


@dataclass
class QueryEntity(BaseEntity):
    query_text: str
    operation: QueryOperation
    language_key: str
    database_type: str
    dialect: QueryDialect
    is_transactional: bool
    is_read_only: bool
    source_file: str
    source_method: str
    line_number: int
    tables_referenced: list[str] = field(default_factory=list)
    columns_referenced: list[str] = field(default_factory=list)
    procedures_called: list[str] = field(default_factory=list)
    functions_called: list[str] = field(default_factory=list)
    views_referenced: list[str] = field(default_factory=list)

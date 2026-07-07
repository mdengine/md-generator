from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from md_generator.codeflow.enterprise_ir.base import BaseEntity


@dataclass
class TableEntity(BaseEntity):
    table_name: str
    database_type: str  # Postgres, MySQL, Oracle, etc.
    columns: list[str] = field(default_factory=list)  # Column IDs
    views: list[str] = field(default_factory=list)  # View IDs using it


@dataclass
class ColumnEntity(BaseEntity):
    column_name: str
    table_name: str
    data_type: str = "VARCHAR"
    is_nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    ref_table: str | None = None
    ref_column: str | None = None


@dataclass
class ViewEntity(BaseEntity):
    view_name: str
    query_definition: str | None = None
    base_tables: list[str] = field(default_factory=list)  # Table IDs
    columns: list[str] = field(default_factory=list)  # Column IDs

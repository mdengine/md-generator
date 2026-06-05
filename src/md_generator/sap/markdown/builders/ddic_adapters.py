from __future__ import annotations

from dataclasses import dataclass, field

from md_generator.sap.markdown.semantic_types import (
    SemanticTypeKind,
    semantic_type_from_cds,
    semantic_type_from_ddic,
    semantic_type_for_type_reference,
)


@dataclass
class StructureComponent:
    name: str
    type_name: str = ""
    type_kind: str = ""
    data_element: str = ""
    data_type: str = ""
    length: int = 0
    semantic_type: SemanticTypeKind = SemanticTypeKind.SCALAR
    children: list[StructureComponent] = field(default_factory=list)


@dataclass
class StructureView:
    name: str
    description: str = ""
    package: str = ""
    definition_source: str = ""
    enhancement_category: str = ""
    components: list[StructureComponent] = field(default_factory=list)


@dataclass
class DataElementView:
    name: str
    description: str = ""
    package: str = ""
    type_kind: str = ""
    type_name: str = ""
    data_type: str = ""
    data_type_length: int = 0
    data_type_decimals: int = 0
    short_field_label: str = ""
    medium_field_label: str = ""
    long_field_label: str = ""
    heading_field_label: str = ""
    search_help: str = ""
    resolved_type: dict = field(default_factory=dict)

    @property
    def semantic_type(self) -> SemanticTypeKind:
        return semantic_type_for_type_reference(self.type_kind)


@dataclass
class DomainView:
    name: str
    description: str = ""
    package: str = ""
    data_type: str = ""
    length: int = 0
    decimals: int = 0
    output_length: int = 0
    value_table: str = ""
    conversion_routine: str = ""
    lower_case: bool = False
    sign_flag: bool = False


@dataclass
class TableFieldView:
    name: str
    data_type: str = ""
    length: int = 0
    key: bool = False
    domain: str = ""
    data_element: str = ""
    check_table: str = ""
    semantic_type: SemanticTypeKind = SemanticTypeKind.SCALAR


@dataclass
class TableView:
    name: str
    description: str = ""
    package: str = ""
    table_type: str = ""
    definition_source: str = ""
    fields: list[TableFieldView] = field(default_factory=list)


@dataclass
class TableTypeView:
    name: str
    description: str = ""
    package: str = ""
    row_type: str = ""
    line_type: str = ""
    access_mode: str = ""
    primary_key: list[str] = field(default_factory=list)


@dataclass
class RangeTypeView:
    name: str
    description: str = ""
    package: str = ""
    data_element: str = ""
    domain: str = ""
    length: int = 0
    decimals: int = 0


@dataclass
class ReferenceTypeView:
    name: str
    description: str = ""
    package: str = ""
    referenced_type: str = ""
    check_table: str = ""


def structure_view_from_ddic(meta: dict) -> StructureView:
    components = [
        StructureComponent(
            name=c.get("name", ""),
            type_name=c.get("type_name", ""),
            type_kind=c.get("type_kind", ""),
            data_element=c.get("data_element", ""),
            data_type=c.get("data_type", ""),
            length=int(c.get("length") or 0),
            semantic_type=semantic_type_from_ddic(c.get("type_kind", ""), c.get("data_type", "")),
        )
        for c in meta.get("components", []) or []
    ]
    return StructureView(
        name=meta.get("name", ""),
        description=meta.get("description", ""),
        package=meta.get("package", ""),
        definition_source=meta.get("definition_source", "adt_xml"),
        components=components,
    )


def structure_view_from_cds(meta: dict) -> StructureView:
    components = [
        StructureComponent(
            name=c.get("name", ""),
            type_name=c.get("type_name", ""),
            type_kind=c.get("type_kind", "type"),
            semantic_type=semantic_type_from_cds(c.get("type_kind", "type")),
        )
        for c in meta.get("components", []) or []
    ]
    return StructureView(
        name=meta.get("name", ""),
        description=meta.get("description", ""),
        package=meta.get("package", ""),
        definition_source=meta.get("definition_source", "cds_ddl"),
        enhancement_category=meta.get("enhancement_category", ""),
        components=components,
    )


def data_element_view_from_raw(meta: dict) -> DataElementView:
    return DataElementView(
        name=meta.get("name", ""),
        description=meta.get("description", ""),
        package=meta.get("package", ""),
        type_kind=meta.get("type_kind", ""),
        type_name=meta.get("type_name", ""),
        data_type=meta.get("data_type", ""),
        data_type_length=int(meta.get("data_type_length") or 0),
        data_type_decimals=int(meta.get("data_type_decimals") or 0),
        short_field_label=meta.get("short_field_label", ""),
        medium_field_label=meta.get("medium_field_label", ""),
        long_field_label=meta.get("long_field_label", ""),
        heading_field_label=meta.get("heading_field_label", ""),
        search_help=meta.get("search_help", ""),
        resolved_type=dict(meta.get("resolved_type") or {}),
    )


def domain_view_from_raw(meta: dict) -> DomainView:
    return DomainView(
        name=meta.get("name", ""),
        description=meta.get("description", ""),
        package=meta.get("package", ""),
        data_type=meta.get("data_type", ""),
        length=int(meta.get("length") or 0),
        decimals=int(meta.get("decimals") or 0),
        output_length=int(meta.get("output_length") or 0),
        value_table=meta.get("value_table", ""),
        conversion_routine=meta.get("conversion_routine", ""),
        lower_case=bool(meta.get("lower_case")),
        sign_flag=bool(meta.get("sign_flag")),
    )


def table_view_from_raw(meta: dict) -> TableView:
    fields = [
        TableFieldView(
            name=f.get("name", ""),
            data_type=f.get("data_type", ""),
            length=int(f.get("length") or 0),
            key=bool(f.get("key")),
            domain=f.get("domain", ""),
            data_element=f.get("data_element", ""),
            check_table=f.get("check_table", ""),
            semantic_type=SemanticTypeKind.SCALAR,
        )
        for f in meta.get("fields", []) or []
    ]
    return TableView(
        name=meta.get("name", ""),
        description=meta.get("description", ""),
        package=meta.get("package", ""),
        table_type=meta.get("table_type", ""),
        definition_source=meta.get("definition_source", ""),
        fields=fields,
    )


def table_type_view_from_raw(meta: dict) -> TableTypeView:
    return TableTypeView(
        name=meta.get("name", ""),
        description=meta.get("description", ""),
        package=meta.get("package", ""),
        row_type=meta.get("row_type", ""),
        line_type=meta.get("line_type", ""),
        access_mode=meta.get("access_mode", ""),
        primary_key=list(meta.get("primary_key") or []),
    )


def range_type_view_from_raw(meta: dict) -> RangeTypeView:
    return RangeTypeView(
        name=meta.get("name", ""),
        description=meta.get("description", ""),
        package=meta.get("package", ""),
        data_element=meta.get("data_element", ""),
        domain=meta.get("domain", ""),
        length=int(meta.get("length") or 0),
        decimals=int(meta.get("decimals") or 0),
    )


def reference_type_view_from_raw(meta: dict) -> ReferenceTypeView:
    return ReferenceTypeView(
        name=meta.get("name", ""),
        description=meta.get("description", ""),
        package=meta.get("package", ""),
        referenced_type=meta.get("referenced_type", ""),
        check_table=meta.get("check_table", ""),
    )

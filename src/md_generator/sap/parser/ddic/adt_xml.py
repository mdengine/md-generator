from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from md_generator.sap.models.metadata.ddic import (
    DdicComponent,
    DdicDataElement,
    DdicDomain,
    DdicField,
    DdicRangeType,
    DdicReferenceType,
    DdicStructure,
    DdicTable,
    DdicTableType,
)

_ADT_MARKERS = (
    'type="DTEL/DE"',
    'type="DOMA/DD"',
    'type="TABL/DT"',
    'type="TABL/DS"',
    'type="TTYP/DA"',
    'type="RSDT/RS"',
    'type="REFT/RT"',
    "dictionary/dtel",
    "dictionary/dom",
    "dictionary/tabl",
    "dictionary/ttyp",
    "dictionary/rsdt",
    "dictionary/reft",
    "dtel:dataelement",
    "doma:domain",
    "tabl:table",
    "tabl:structure",
    "ttyp:tabletype",
    "rsdt:rangestype",
    "reft:referencetype",
)


def _local(tag: str) -> str:
    if not isinstance(tag, str):
        return str(tag)
    return tag.split("}")[-1] if "}" in tag else tag


def _attr(elem: ET.Element, name: str, default: str = "") -> str:
    for key, value in elem.attrib.items():
        local = key.split("}")[-1] if "}" in key else key.split(":")[-1]
        if local == name:
            return (value or "").strip()
    return default


def _child_text(parent: ET.Element, local_name: str, default: str = "") -> str:
    for child in parent:
        if _local(child.tag) == local_name:
            return (child.text or "").strip()
    return default


def _int_text(parent: ET.Element, local_name: str, default: int = 0) -> int:
    raw = _child_text(parent, local_name, "")
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _bool_text(parent: ET.Element, local_name: str) -> bool:
    return _child_text(parent, local_name, "").lower() == "true"


def _root_meta(root: ET.Element) -> tuple[str, str, str, str]:
    return (
        _attr(root, "type"),
        _attr(root, "name").upper(),
        _attr(root, "description"),
        "",
    )


def _package(root: ET.Element) -> str:
    for child in root:
        if _local(child.tag) == "packageRef":
            return _attr(child, "name")
    return ""


def is_adt_ddic_xml(path: Path) -> bool:
    if path.suffix.lower() != ".xml":
        return False
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:4096]
    except OSError:
        return False
    lower = head.lower()
    if _is_odata_or_hana_xml(lower):
        return False
    if "wbobj/dictionary" not in lower and not any(m.lower() in lower for m in _ADT_MARKERS):
        return False
    return any(marker.lower() in lower for marker in _ADT_MARKERS)


def _is_odata_or_hana_xml(lower: str) -> bool:
    if "edmx" in lower or "edm:" in lower:
        return True
    if "calculation:scenario" in lower or "calculationscenario" in lower:
        return True
    if "analyticview" in lower or "attributeview" in lower:
        return True
    return False


def parse_adt_ddic_xml(text: str) -> dict[str, Any] | None:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return None

    obj_type, name, description, _ = _root_meta(root)
    package = _package(root)

    if obj_type == "DTEL/DE" or _find_payload(root, "dataElement") is not None:
        payload = _find_payload(root, "dataElement")
        if payload is None:
            return None
        return {"object_kind": "DATA_ELEMENT", "data_element": _parse_data_element(name, description, package, payload).to_dict()}

    if obj_type == "DOMA/DD" or _find_payload(root, "domain") is not None:
        payload = _find_payload(root, "domain")
        if payload is None:
            return None
        return {"object_kind": "DOMAIN", "domain": _parse_domain(name, description, package, payload).to_dict()}

    if obj_type == "TABL/DS" or _find_payload(root, "structure") is not None:
        payload = _find_payload(root, "structure")
        if payload is None:
            return None
        return {"object_kind": "STRUCTURE", "structure": _parse_structure(name, description, package, payload).to_dict()}

    if obj_type == "TABL/DT" or _find_payload(root, "table") is not None:
        payload = _find_payload(root, "table")
        if payload is None:
            return None
        return {"object_kind": "TABLE", "ddic": _parse_table(name, description, package, payload).to_dict()}

    if obj_type == "TTYP/DA" or _find_payload(root, "tableType") is not None:
        payload = _find_payload(root, "tableType")
        if payload is None:
            return None
        return {"object_kind": "TABLE_TYPE", "table_type": _parse_table_type(name, description, package, payload).to_dict()}

    if obj_type == "RSDT/RS" or _find_payload(root, "rangesType") is not None:
        payload = _find_payload(root, "rangesType")
        if payload is None:
            return None
        return {"object_kind": "RANGE_TYPE", "range_type": _parse_range_type(name, description, package, payload).to_dict()}

    if obj_type == "REFT/RT" or _find_payload(root, "referenceType") is not None:
        payload = _find_payload(root, "referenceType")
        if payload is None:
            return None
        return {"object_kind": "REFERENCE_TYPE", "reference_type": _parse_reference_type(name, description, package, payload).to_dict()}

    return None


def _find_payload(root: ET.Element, local_name: str) -> ET.Element | None:
    for child in root:
        if _local(child.tag) == local_name:
            return child
    return None


def _parse_components(elem: ET.Element) -> list[DdicComponent]:
    components: list[DdicComponent] = []
    for child in elem:
        tag = _local(child.tag)
        if tag not in ("component", "field"):
            continue
        cname = _child_text(child, "name").upper() or _attr(child, "name").upper()
        if not cname:
            continue
        components.append(
            DdicComponent(
                name=cname,
                data_element=_child_text(child, "dataElement").upper(),
                data_type=_child_text(child, "dataType"),
                type_name=_child_text(child, "typeName").upper(),
                length=_int_text(child, "length"),
            )
        )
    return components


def _parse_data_element(name: str, description: str, package: str, elem: ET.Element) -> DdicDataElement:
    return DdicDataElement(
        name=name,
        description=description,
        package=package,
        type_kind=_child_text(elem, "typeKind"),
        type_name=_child_text(elem, "typeName").upper(),
        data_type=_child_text(elem, "dataType"),
        data_type_length=_int_text(elem, "dataTypeLength"),
        data_type_decimals=_int_text(elem, "dataTypeDecimals"),
        short_field_label=_child_text(elem, "shortFieldLabel"),
        medium_field_label=_child_text(elem, "mediumFieldLabel"),
        long_field_label=_child_text(elem, "longFieldLabel"),
        heading_field_label=_child_text(elem, "headingFieldLabel"),
        search_help=_child_text(elem, "searchHelp"),
        change_document=_bool_text(elem, "changeDocument"),
    )


def _parse_domain(name: str, description: str, package: str, elem: ET.Element) -> DdicDomain:
    return DdicDomain(
        name=name,
        description=description,
        package=package,
        data_type=_child_text(elem, "dataType"),
        length=_int_text(elem, "length") or _int_text(elem, "dataTypeLength"),
        decimals=_int_text(elem, "decimals") or _int_text(elem, "dataTypeDecimals"),
        output_length=_int_text(elem, "outputLength"),
        value_table=_child_text(elem, "valueTable").upper(),
        conversion_routine=_child_text(elem, "conversionRoutine"),
        lower_case=_bool_text(elem, "lowerCase"),
        sign_flag=_bool_text(elem, "signFlag"),
    )


def _parse_structure(name: str, description: str, package: str, elem: ET.Element) -> DdicStructure:
    return DdicStructure(
        name=name,
        description=description,
        package=package,
        components=_parse_components(elem),
    )


def _parse_table(name: str, description: str, package: str, elem: ET.Element) -> DdicTable:
    tbl = DdicTable(name=name, description=description, package=package, definition_source="adt_xml")
    for comp in _parse_components(elem):
        key = False
        fld = DdicField(
            name=comp.name,
            data_type=comp.data_type,
            length=comp.length,
            key=key,
            data_element=comp.data_element,
        )
        tbl.fields.append(fld)
    for child in elem:
        if _local(child.tag) != "field":
            continue
        fname = _child_text(child, "name").upper() or _attr(child, "name").upper()
        if not fname or any(f.name == fname for f in tbl.fields):
            continue
        key = _bool_text(child, "key") or _child_text(child, "keyFlag").upper() == "X"
        fld = DdicField(
            name=fname,
            data_type=_child_text(child, "dataType"),
            length=_int_text(child, "length"),
            key=key,
            domain=_child_text(child, "domain").upper(),
            data_element=_child_text(child, "dataElement").upper(),
            check_table=_child_text(child, "checkTable").upper(),
        )
        tbl.fields.append(fld)
        if key and fname not in tbl.primary_key:
            tbl.primary_key.append(fname)
    return tbl


def _parse_table_type(name: str, description: str, package: str, elem: ET.Element) -> DdicTableType:
    pk: list[str] = []
    for child in elem:
        if _local(child.tag) == "keyComponent":
            kn = _child_text(child, "name").upper()
            if kn:
                pk.append(kn)
    return DdicTableType(
        name=name,
        description=description,
        package=package,
        row_type=_child_text(elem, "rowType").upper(),
        line_type=_child_text(elem, "lineType").upper(),
        access_mode=_child_text(elem, "accessMode"),
        primary_key=pk,
    )


def _parse_range_type(name: str, description: str, package: str, elem: ET.Element) -> DdicRangeType:
    return DdicRangeType(
        name=name,
        description=description,
        package=package,
        data_element=_child_text(elem, "dataElement").upper(),
        domain=_child_text(elem, "domain").upper(),
        length=_int_text(elem, "length"),
        decimals=_int_text(elem, "decimals"),
    )


def _parse_reference_type(name: str, description: str, package: str, elem: ET.Element) -> DdicReferenceType:
    return DdicReferenceType(
        name=name,
        description=description,
        package=package,
        referenced_type=_child_text(elem, "referencedType").upper() or _child_text(elem, "typeName").upper(),
        check_table=_child_text(elem, "checkTable").upper(),
    )


def parse_adt_ddic_file(path: Path) -> dict[str, Any] | None:
    return parse_adt_ddic_xml(path.read_text(encoding="utf-8", errors="replace"))

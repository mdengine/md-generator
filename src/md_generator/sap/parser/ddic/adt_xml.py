from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from md_generator.sap.models.metadata.ddic import DdicDataElement, DdicDomain, DdicField, DdicTable


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


def is_adt_ddic_xml(path: Path) -> bool:
    if path.suffix.lower() != ".xml":
        return False
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:4096]
    except OSError:
        return False
    lower = head.lower()
    if "wbobj/dictionary" not in lower and "dtel:dataelement" not in lower:
        if "doma:domain" not in lower and "tabl:table" not in lower:
            return False
    if _is_odata_or_hana_xml(lower):
        return False
    return any(
        marker in head
        for marker in (
            'type="DTEL/DE"',
            "type=\"DOMA/DD\"",
            'type="TABL/DT"',
            "dictionary/dtel",
            "dictionary/dom",
            "dictionary/tabl",
        )
    )


def _is_odata_or_hana_xml(lower: str) -> bool:
    if "edmx" in lower or "edm:" in lower:
        return True
    if "calculation:scenario" in lower or "calculationscenario" in lower:
        return True
    if "analyticview" in lower or "attributeview" in lower:
        return True
    return False


def parse_adt_ddic_xml(text: str) -> dict[str, Any] | None:
    """Parse SAP ADT DDIC wbobj XML; returns dict with object_kind and metadata."""
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return None

    obj_type = _attr(root, "type")
    name = _attr(root, "name").upper()
    description = _attr(root, "description")
    package = ""
    for child in root:
        if _local(child.tag) == "packageRef":
            package = _attr(child, "name")
            break

    if obj_type == "DTEL/DE" or _find_payload(root, "dataElement") is not None:
        payload = _find_payload(root, "dataElement")
        if payload is None:
            return None
        de = _parse_data_element(name, description, package, payload)
        return {"object_kind": "DATA_ELEMENT", "data_element": de.to_dict()}

    if obj_type == "DOMA/DD" or _find_payload(root, "domain") is not None:
        payload = _find_payload(root, "domain")
        if payload is None:
            return None
        dom = _parse_domain(name, description, package, payload)
        return {"object_kind": "DOMAIN", "domain": dom.to_dict()}

    if obj_type == "TABL/DT" or _find_payload(root, "table") is not None:
        payload = _find_payload(root, "table")
        if payload is None:
            return None
        tbl = _parse_table(name, description, package, payload)
        return {"object_kind": "TABLE", "ddic": tbl.to_dict()}

    return None


def _find_payload(root: ET.Element, local_name: str) -> ET.Element | None:
    for child in root:
        if _local(child.tag) == local_name:
            return child
    return None


def _parse_data_element(
    name: str,
    description: str,
    package: str,
    elem: ET.Element,
) -> DdicDataElement:
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


def _parse_domain(
    name: str,
    description: str,
    package: str,
    elem: ET.Element,
) -> DdicDomain:
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


def _parse_table(
    name: str,
    description: str,
    package: str,
    elem: ET.Element,
) -> DdicTable:
    tbl = DdicTable(name=name, description=description, package=package)
    for child in elem:
        if _local(child.tag) != "field":
            continue
        fname = _child_text(child, "name").upper() or _attr(child, "name").upper()
        if not fname:
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


def parse_adt_ddic_file(path: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    return parse_adt_ddic_xml(text)

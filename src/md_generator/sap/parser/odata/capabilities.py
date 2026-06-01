from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from md_generator.sap.models.metadata.odata import ODataCapabilities
from md_generator.sap.parser.odata import namespaces as ns


def _bool_attr(elem: ET.Element | None, attr: str) -> bool | None:
    if elem is None:
        return None
    val = elem.get(attr)
    if val is None:
        return None
    return val.lower() not in ("false", "0")


def parse_capabilities_from_annotations(annotations: list[ET.Element]) -> ODataCapabilities:
    cap = ODataCapabilities()
    for ann in annotations:
        term = ns.annotation_term(ann)
        if "InsertRestrictions" in term:
            cap.insertable = _bool_attr(ann, "Insertable")
        elif "DeleteRestrictions" in term:
            cap.deletable = _bool_attr(ann, "Deletable")
        elif "UpdateRestrictions" in term:
            cap.updatable = _bool_attr(ann, "Updatable")
        elif "SearchRestrictions" in term:
            cap.searchable = _bool_attr(ann, "Searchable")
        elif "FilterRestrictions" in term:
            cap.filterable = True
            for child in ann:
                if ns.local_name(child.tag) == "FilterFunction":
                    fn = child.get("Name") or child.text
                    if fn:
                        cap.filter_functions.append(fn)
        elif "SortRestrictions" in term:
            cap.sortable = True
        elif "ExpandRestrictions" in term:
            cap.expandable = True
    return cap


def parse_capabilities_json(annotations: list[dict[str, Any]]) -> ODataCapabilities:
    cap = ODataCapabilities()
    for ann in annotations:
        term = str(ann.get("term") or ann.get("@term") or "")
        if "InsertRestrictions" in term:
            cap.insertable = ann.get("Insertable", ann.get("insertable"))
        elif "DeleteRestrictions" in term:
            cap.deletable = ann.get("Deletable", ann.get("deletable"))
        elif "UpdateRestrictions" in term:
            cap.updatable = ann.get("Updatable", ann.get("updatable"))
        elif "SearchRestrictions" in term:
            cap.searchable = ann.get("Searchable", ann.get("searchable"))
        elif "FilterRestrictions" in term:
            cap.filterable = True
        elif "SortRestrictions" in term:
            cap.sortable = True
        elif "ExpandRestrictions" in term:
            cap.expandable = True
    return cap

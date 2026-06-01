from __future__ import annotations

import xml.etree.ElementTree as ET

EDMX_NS_V1 = "http://schemas.microsoft.com/ado/2007/06/edmx"
EDMX_NS_V4 = "http://docs.oasis-open.org/odata/ns/edmx"
EDM_NS_V1 = "http://schemas.microsoft.com/ado/2008/09/edm"
EDM_NS_V4 = "http://docs.oasis-open.org/odata/ns/edm"
M_NS = "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
CAPABILITIES_V1 = "Org.OData.Capabilities.V1"
CORE_V1 = "Org.OData.Core.V1"

KNOWN_EDM = frozenset({EDM_NS_V1, EDM_NS_V4})


def local_name(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def find_children(elem: ET.Element, local: str) -> list[ET.Element]:
    return [c for c in elem if local_name(c.tag) == local]


def find_descendants(root: ET.Element, local: str) -> list[ET.Element]:
    return [e for e in root.iter() if local_name(e.tag) == local]


def schema_namespace(schema_elem: ET.Element) -> str:
    return schema_elem.get("Namespace") or ""


def annotation_term(ann_elem: ET.Element) -> str:
    term = ann_elem.get("Term") or ""
    if term:
        return term
    return local_name(ann_elem.tag)

from __future__ import annotations

import xml.etree.ElementTree as ET

from md_generator.sap.parser.odata import namespaces as ns


def test_local_name():
    assert ns.local_name("{http://example.com}Schema") == "Schema"
    assert ns.local_name("Schema") == "Schema"


def test_find_children():
    root = ET.fromstring(
        '<Schema xmlns="http://schemas.microsoft.com/ado/2008/09/edm">'
        '<EntityType Name="A"/><ComplexType Name="B"/>'
        "</Schema>"
    )
    ets = ns.find_children(root, "EntityType")
    assert len(ets) == 1
    assert ets[0].get("Name") == "A"


def test_schema_namespace():
    root = ET.fromstring(
        '<Schema Namespace="SAP" xmlns="http://schemas.microsoft.com/ado/2008/09/edm"/>'
    )
    assert ns.schema_namespace(root) == "SAP"

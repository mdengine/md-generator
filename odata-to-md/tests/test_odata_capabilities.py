from __future__ import annotations

import xml.etree.ElementTree as ET

from md_generator.odata.parser.capabilities import (
    parse_capabilities_from_annotations,
    parse_capabilities_json,
)


def test_xml_insert_restrictions():
    ann = ET.fromstring(
        '<Annotation Term="Org.OData.Capabilities.V1.InsertRestrictions" Insertable="true"/>'
    )
    cap = parse_capabilities_from_annotations([ann])
    assert cap.insertable is True


def test_xml_search_restrictions():
    ann = ET.fromstring(
        '<Annotation Term="Org.OData.Capabilities.V1.SearchRestrictions" Searchable="true"/>'
    )
    cap = parse_capabilities_from_annotations([ann])
    assert cap.searchable is True


def test_json_capabilities():
    cap = parse_capabilities_json(
        [{"term": "Org.OData.Capabilities.V1.InsertRestrictions", "Insertable": True}]
    )
    assert cap.insertable is True


def test_query_options_from_capabilities():
    from md_generator.odata.models.domain import ODataCapabilities, ODataVersion

    cap = ODataCapabilities(filterable=True, searchable=True, sortable=True)
    opts = cap.supported_query_options(ODataVersion.V4)
    assert "$filter" in opts
    assert "$search" in opts
    assert "$orderby" in opts

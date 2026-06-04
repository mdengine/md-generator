from __future__ import annotations

from pathlib import Path
from typing import Protocol

from md_generator.odata.models.domain import ODataFormat, ODataMetadataDocument, ODataVersion
from md_generator.odata.parser.detector import detect_format, detect_version
from md_generator.odata.parser.json.v4 import parse_v4_json
from md_generator.odata.parser.xml.v1 import parse_v1_xml
from md_generator.odata.parser.xml.v2_v3 import parse_v2_v3_xml
from md_generator.odata.parser.xml.v4 import parse_v4_xml


class ODataVersionParser(Protocol):
    def parse(self, path: Path, text: str | None = None) -> ODataMetadataDocument: ...


class V1Parser:
    def parse(self, path: Path, text: str | None = None) -> ODataMetadataDocument:
        return parse_v1_xml(path, text)


class V2V3Parser:
    def __init__(self, version: ODataVersion) -> None:
        self._version = version

    def parse(self, path: Path, text: str | None = None) -> ODataMetadataDocument:
        return parse_v2_v3_xml(path, self._version, text)


class V4XMLParser:
    def parse(self, path: Path, text: str | None = None) -> ODataMetadataDocument:
        return parse_v4_xml(path, text)


class V4JSONParser:
    def parse(self, path: Path, text: str | None = None) -> ODataMetadataDocument:
        return parse_v4_json(path, text)


def get_parser(version: ODataVersion, fmt: ODataFormat) -> ODataVersionParser:
    if fmt == ODataFormat.CSDL_JSON:
        return V4JSONParser()
    if version == ODataVersion.V1:
        return V1Parser()
    if version in (ODataVersion.V2, ODataVersion.V3):
        return V2V3Parser(version)
    if version == ODataVersion.V4:
        return V4XMLParser()
    return V2V3Parser(ODataVersion.V2)


def parse_document(path: Path, text: str | None = None) -> ODataMetadataDocument:
    raw = text if text is not None else path.read_text(encoding="utf-8", errors="replace")
    fmt = detect_format(path, raw)
    version = detect_version(path, fmt, raw)
    if version == ODataVersion.UNKNOWN and fmt == ODataFormat.EDMX_XML:
        version = ODataVersion.V2
    parser = get_parser(version, fmt)
    doc = parser.parse(path, raw)
    if not doc.metadata_url:
        doc.metadata_url = str(path)
    return doc

from __future__ import annotations

from pathlib import Path

from md_generator.sap.models.metadata.odata import ODataMetadataDocument
from md_generator.sap.parser.base import ParseContext, SapParseResult
from md_generator.sap.parser.odata.document_to_objects import document_to_sap_objects
from md_generator.sap.parser.odata.legacy import document_to_legacy_entities
from md_generator.sap.parser.odata.registry import parse_document


def parse_odata_metadata(path: Path) -> tuple[str, list[dict]]:
    """Legacy API: service name + entity dict list (backward compatible)."""
    doc = parse_document(path)
    return doc.service_name, document_to_legacy_entities(doc)


def parse_odata_metadata_document(path: Path, text: str | None = None) -> ODataMetadataDocument:
    return parse_document(path, text)


def _is_odata_metadata(path: Path) -> bool:
    n = path.name.lower()
    if n in ("$metadata.xml", "metadata.xml", "$metadata", "metadata.json", "$metadata.json"):
        return True
    if path.suffix.lower() in {".edmx"}:
        return True
    if path.suffix.lower() == ".xml" and "metadata" in n:
        return True
    if path.suffix.lower() == ".json":
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")[:4096]
            if "@odata.context" in raw or "$EntityType" in raw:
                return True
        except OSError:
            pass
    return False


class ODataParserPlugin:
    name = "odata"

    def can_parse(self, path: Path) -> bool:
        n = path.name.lower()
        if "bapi" in n and path.suffix.lower() == ".json":
            return False
        return _is_odata_metadata(path)

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult:
        doc = parse_document(path)
        objects = document_to_sap_objects(doc, path, ctx.package_hint)
        return SapParseResult(
            path=path,
            objects=objects,
            metadata={
                "odata_entities": document_to_legacy_entities(doc),
                "odata_document": doc.to_dict(),
            },
        )

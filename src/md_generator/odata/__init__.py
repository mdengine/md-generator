"""Shared OData metadata parsing, catalog generation, and optional graph/chunks."""

from md_generator.odata.fetch import fetch_metadata, infer_service_root
from md_generator.odata.models.domain import ODataMetadataDocument, ODataVersion
from md_generator.odata.parser.registry import parse_document
from md_generator.odata.writers.catalog_writer import render_odata_catalog

__all__ = [
    "ODataMetadataDocument",
    "ODataVersion",
    "fetch_metadata",
    "infer_service_root",
    "parse_document",
    "render_odata_catalog",
]

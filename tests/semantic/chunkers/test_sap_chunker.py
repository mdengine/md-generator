"""Tests for SAP ABAP function module chunker."""

import hashlib
from md_generator.semantic.chunkers.sap import SAPChunker
from md_generator.semantic.model.schema import CanonicalMetadata, SemanticDocument


def _make_doc_id(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def test_sap_function_module_chunking():
    chunker = SAPChunker()
    abap_code = """
FUNCTION Z_PROCESS_PAYMENT.
*"----------------------------------------------------------------------
*"  Processing payment order
*"----------------------------------------------------------------------
  WRITE: / 'Processing order'.
ENDFUNCTION.

FUNCTION Z_VALIDATE_CUSTOMER.
  WRITE: / 'Validating customer'.
ENDFUNCTION.
"""

    doc = SemanticDocument(
        document_id=_make_doc_id("doc-sap-1"),
        sanitized_content=abap_code,
        metadata=CanonicalMetadata(source_uri="file:///z_payment.abap", source_type="abap"),
    )

    chunks = chunker.chunk_document(doc)
    assert len(chunks) == 2
    symbols = [c.metadata.symbol_name for c in chunks if c.metadata]
    assert "Z_PROCESS_PAYMENT" in symbols
    assert "Z_VALIDATE_CUSTOMER" in symbols


def test_sap_symbol_extraction():
    chunker = SAPChunker()
    abap_code = "FUNCTION Z_TEST. WRITE: / 'Test'. ENDFUNCTION."

    doc = SemanticDocument(
        document_id=_make_doc_id("doc-sap-2"),
        sanitized_content=abap_code,
        metadata=CanonicalMetadata(source_uri="file:///z_test.abap", source_type="abap"),
    )

    res = chunker.extract_symbols(doc)
    assert len(res.entities) == 1
    assert res.entities[0].entity_type == "SAP_OBJECT"
    assert res.entities[0].name == "Z_TEST"

"""Test Suite for ContextualDocumentChunker in md_generator.semantic.chunkers.

Verifies:
1. Strict schema compliance for SemanticChunk, ChunkLineage, and SourceLocation.
2. PDF page chunking with SourceLocation(location_type='pdf', page=N).
3. PPTX slide chunking with SourceLocation(location_type='pptx', slide=N).
4. Stable chunk identity: chunk IDs remain stable across document insertions.
5. Hierarchical parent-child linking (Document -> Page/Slide -> Paragraph/Table/Image).
6. Table and Image OCR block extraction.
7. Overlapping sentence boundary preservation (15% overlap).
8. Seamless ChunkerRegistry integration with zero regression.
"""

import pytest
from md_generator.lineage.ids import generate_document_id
from md_generator.semantic.chunkers.document import (
    ContextualDocumentChunker,
    DocumentChunkerConfig,
)
from md_generator.semantic.chunkers.registry import ChunkerRegistry
from md_generator.semantic.model.schema import (
    CanonicalMetadata,
    SemanticChunk,
    SemanticDocument,
)

SAMPLE_DOC_ID = "1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff"


def _make_doc(content: str, source_type: str = "doc.pdf", source_uri: str = "file:///c:/docs/test.pdf") -> SemanticDocument:
    meta = CanonicalMetadata(
        source_type=source_type,
        source_uri=source_uri,
        source_path="/docs/test.pdf",
    )
    return SemanticDocument(
        schema_version="1.0",
        document_id=SAMPLE_DOC_ID,
        sanitized_content=content,
        document_type="document",
        metadata=meta,
    )


def test_pdf_page_chunking_and_schema_compliance():
    content = """# Document Title

## Page 1
This is the first page of the PDF document. It contains important installation instructions.
Make sure to connect the fiber cable before powering on the terminal.

| Step | Action | Status |
|---|---|---|
| 1 | Connect Cable | Done |
| 2 | Power On | Pending |

## Page 2
This is the second page of the PDF document. It contains troubleshooting steps.
If the optical loss exceeds -25 dBm, contact central support immediately.
"""
    doc = _make_doc(content, source_type="doc.pdf", source_uri="file:///c:/docs/network.pdf")
    chunker = ContextualDocumentChunker()
    chunks = chunker.chunk_document(doc)

    assert len(chunks) >= 4  # Doc root + Page 1 + Page 2 + Table 1 (+ possible paragraphs)

    # All chunks must pass strict schema validation
    for c in chunks:
        c.validate()
        assert len(c.chunk_id) == 64
        assert c.document_id == SAMPLE_DOC_ID
        assert c.lineage is not None
        assert c.lineage.location is not None
        assert c.lineage.location.location_type == "pdf"

    # Verify Page 1 chunk
    p1_chunks = [c for c in chunks if c.lineage.location.page == 1 and "## Page 1" in c.sanitized_content]
    assert len(p1_chunks) == 1
    p1 = p1_chunks[0]
    assert p1.lineage.location.page == 1

    # Verify Table child chunk (specifically the dedicated table chunk)
    table_child_chunks = [
        c for c in chunks
        if c.lineage.parent_chunk_id == p1.chunk_id and c.sanitized_content.strip().startswith("| Step | Action |")
    ]
    assert len(table_child_chunks) == 1
    tbl = table_child_chunks[0]
    assert tbl.lineage.parent_chunk_id == p1.chunk_id
    assert tbl.lineage.location.page == 1


def test_pptx_slide_chunking():
    content = """# Executive Briefing

## Slide 1: Welcome and Agenda
Welcome to the enterprise quarterly architecture review.
We will discuss scaling, edge caching, and knowledge graphs.

## Slide 2: Multi-Cloud Topology
Overview of multi-cloud Kubernetes clusters across AWS and GCP.
Zero single point of failure with automatic failover.
"""
    doc = _make_doc(content, source_type="doc.pptx", source_uri="file:///c:/slides/briefing.pptx")
    chunker = ContextualDocumentChunker()
    chunks = chunker.chunk_document(doc)

    assert len(chunks) >= 3  # Root + Slide 1 + Slide 2

    # Verify Slide 1 & Slide 2 location types
    slide1_chunks = [c for c in chunks if c.lineage and c.lineage.location and c.lineage.location.slide == 1]
    slide2_chunks = [c for c in chunks if c.lineage and c.lineage.location and c.lineage.location.slide == 2]

    assert len(slide1_chunks) >= 1
    assert len(slide2_chunks) >= 1

    s1 = slide1_chunks[0]
    assert s1.lineage.location.location_type == "pptx"
    assert s1.lineage.location.slide == 1
    assert s1.lineage.location.page is None  # Must NOT set page for pptx!


def test_stable_chunk_ids_across_insertions():
    """Verify that adding an extra section does not change the ID of existing unchanged chunks."""
    content_v1 = """## Page 1
Original page 1 content that should have a stable identifier.

## Page 2
Original page 2 content that should also remain stable.
"""
    doc_v1 = _make_doc(content_v1)
    chunker = ContextualDocumentChunker()
    chunks_v1 = chunker.chunk_document(doc_v1)

    p1_v1 = next(c for c in chunks_v1 if c.lineage.location.page == 1 and "## Page 1" in c.sanitized_content)
    p2_v1 = next(c for c in chunks_v1 if c.lineage.location.page == 2 and "## Page 2" in c.sanitized_content)

    # v2: An extra page is inserted at the beginning (Page 0)
    content_v2 = """## Page 0
Newly prepended cover page.

## Page 1
Original page 1 content that should have a stable identifier.

## Page 2
Original page 2 content that should also remain stable.
"""
    doc_v2 = _make_doc(content_v2)
    chunks_v2 = chunker.chunk_document(doc_v2)

    p1_v2 = next(c for c in chunks_v2 if c.lineage.location.page == 1 and "## Page 1" in c.sanitized_content)
    p2_v2 = next(c for c in chunks_v2 if c.lineage.location.page == 2 and "## Page 2" in c.sanitized_content)

    # The chunk IDs for Page 1 and Page 2 must remain 100% IDENTICAL
    assert p1_v1.chunk_id == p1_v2.chunk_id
    assert p2_v1.chunk_id == p2_v2.chunk_id


def test_stable_paragraph_and_table_chunk_ids_on_insertion():
    """Verify that inserting a new paragraph does not alter the ID of an unchanged table or paragraph."""
    content_v1 = """## Page 1
First paragraph explaining the system.

| Metric | Target |
|---|---|
| Latency | <10ms |
"""
    doc_v1 = _make_doc(content_v1)
    chunker = ContextualDocumentChunker()
    chunks_v1 = chunker.chunk_document(doc_v1)

    table_v1 = next(c for c in chunks_v1 if c.sanitized_content.strip().startswith("| Metric | Target |"))

    # v2: An extra paragraph is prepended before the table
    content_v2 = """## Page 1
Newly inserted notice at the top of the page.

First paragraph explaining the system.

| Metric | Target |
|---|---|
| Latency | <10ms |
"""
    doc_v2 = _make_doc(content_v2)
    chunks_v2 = chunker.chunk_document(doc_v2)

    table_v2 = next(c for c in chunks_v2 if c.sanitized_content.strip().startswith("| Metric | Target |"))

    # Table chunk ID must remain 100% identical
    assert table_v1.chunk_id == table_v2.chunk_id


def test_image_ocr_child_chunk_extraction():
    content = """## Page 1
Architectural layout showing the primary fiber node and splitter.

![Topology Diagram](images/doc/page_1_img_0.png)
> **Extracted OCR Text**: Splitter 1:8 Loss: -3.2dB Node ID: AF-509
"""
    doc = _make_doc(content)
    chunker = ContextualDocumentChunker()
    chunks = chunker.chunk_document(doc)

    # Find the child image/OCR chunk (parent_chunk_id is not None)
    img_child_chunks = [
        c for c in chunks
        if c.lineage and c.lineage.parent_chunk_id is not None and c.sanitized_content.startswith("![Topology Diagram]")
    ]
    assert len(img_child_chunks) >= 1
    img_c = img_child_chunks[0]
    assert img_c.lineage.location.page == 1
    assert img_c.lineage.parent_chunk_id is not None


def test_overlapping_sentences():
    # Long text exceeding chunk size to trigger overlapping windowing
    sentences = [f"Sentence {i}: Understanding system architecture requires systematic validation." for i in range(50)]
    long_content = "## Page 1\n" + " ".join(sentences)

    cfg = DocumentChunkerConfig(chunk_size=100, overlap_pct=0.15)
    chunker = ContextualDocumentChunker(config=cfg)
    doc = _make_doc(long_content)
    chunks = chunker.chunk_document(doc)

    # Should produce multiple child paragraph chunks
    para_chunks = [c for c in chunks if "Sentence" in c.sanitized_content and c.sanitized_content != long_content]
    assert len(para_chunks) >= 2

    # Check for sentence overlap between consecutive chunks
    overlap_found = False
    for i in range(len(para_chunks) - 1):
        words_a = set(para_chunks[i].sanitized_content.split()[-10:])
        words_b = set(para_chunks[i + 1].sanitized_content.split()[:10])
        if words_a.intersection(words_b):
            overlap_found = True
            break
    assert overlap_found


def test_docx_section_chunking():
    content = """# Section: Project Overview
Detailed overview of the system architecture.

# Section: Deployment Guidelines
Instructions for deploying the application on premise.
"""
    doc = _make_doc(content, source_type="doc.word", source_uri="file:///c:/docs/guide.docx")
    chunker = ContextualDocumentChunker()
    chunks = chunker.chunk_document(doc)

    assert len(chunks) >= 3  # Root + Section 1 + Section 2
    sec_chunks = [c for c in chunks if c.lineage and c.lineage.location and c.lineage.location.location_type == "docx"]
    assert len(sec_chunks) >= 2
    for sc in sec_chunks:
        sc.validate()
        assert sc.lineage.location.location_type == "docx"
        assert sc.lineage.location.page is None
        assert sc.lineage.location.slide is None

    content = """## Page 1
System documentation.

![Architecture Diagram](images/doc/page_1_img_0.png)

## Page 2
Maintenance guide.
"""
    doc = _make_doc(content)
    chunker = ContextualDocumentChunker()
    result = chunker.extract_symbols(doc)

    assert result.parse_status.value == "CLEAN"
    assert len(result.entities) >= 4  # Document, Page 1, Page 2, Image
    assert len(result.relationships) >= 3  # Document CONTAINS Page 1, Page 2; Page 1 REFERENCES_IMAGE


def test_chunker_registry_integration():
    registry = ChunkerRegistry.get_default()

    # Document formats must resolve to ContextualDocumentChunker
    assert isinstance(registry.resolve("doc.pdf"), ContextualDocumentChunker)
    assert isinstance(registry.resolve("pdf"), ContextualDocumentChunker)
    assert isinstance(registry.resolve("doc.pptx"), ContextualDocumentChunker)
    assert isinstance(registry.resolve("pptx"), ContextualDocumentChunker)
    assert isinstance(registry.resolve("doc.word"), ContextualDocumentChunker)
    assert isinstance(registry.resolve("markdown"), ContextualDocumentChunker)
    assert isinstance(registry.resolve("text.plain"), ContextualDocumentChunker)

    # Existing chunkers must STILL resolve correctly
    from md_generator.semantic.chunkers.code import CodeChunker
    from md_generator.semantic.chunkers.openapi import OpenAPIChunker
    from md_generator.semantic.chunkers.sap import SAPChunker
    from md_generator.semantic.chunkers.db import DBChunker

    assert isinstance(registry.resolve("py"), CodeChunker)
    assert isinstance(registry.resolve("openapi"), OpenAPIChunker)
    assert isinstance(registry.resolve("abap"), SAPChunker)
    assert isinstance(registry.resolve("sql"), DBChunker)

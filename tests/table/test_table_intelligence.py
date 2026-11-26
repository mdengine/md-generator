"""Unit tests for Structural Table Intelligence, Parsing, Normalization and Graph Integration (Prompt 07)."""

import pytest

from md_generator.table.models import TableCell, TableData
from md_generator.table.parser import MarkdownTableParser, is_divider_row
from md_generator.table.formatter import format_markdown_table, table_to_html
from md_generator.semantic.chunkers.document import ContextualDocumentChunker
from md_generator.semantic.model.schema import CanonicalMetadata, SemanticDocument, SourceLocation
from md_generator.graph.extractor import extract
from md_generator.graph.reconciler import GraphReconciler
from md_generator.graph.stores.in_memory import InMemoryGraphStore


# ==============================================================================
# 1. Markdown Table Parsing & Normalization Tests
# ==============================================================================

def test_parse_standard_markdown_table():
    """Validates parsing standard GitHub-Flavored Markdown table with headers and divider."""
    md = """# System Specifications

| Server | CPU Cores | RAM (GB) | Storage |
|:---|:---:|---:|---|
| primary-01 | 64 | 256 | 4TB NVMe |
| standby-02 | 32 | 128 | 2TB NVMe |
| backup-03 | 16 | 64 | 8TB HDD |
"""
    tables = MarkdownTableParser.parse_tables(md)
    assert len(tables) == 1
    t = tables[0]

    assert t.headers == ["Server", "CPU Cores", "RAM (GB)", "Storage"]
    assert len(t.rows) == 3
    assert t.rows[0] == ["primary-01", "64", "256", "4TB NVMe"]
    assert t.num_rows == 4  # 1 header + 3 data rows
    assert t.num_cols == 4
    assert t.table_id.startswith("tbl_")

    # Cell lookup
    c_head = t.get_cell(0, 0)
    assert c_head is not None
    assert c_head.is_header is True
    assert c_head.content == "Server"

    c_data = t.get_cell(1, 1)
    assert c_data is not None
    assert c_data.is_header is False
    assert c_data.content == "64"


def test_parse_ragged_table_and_escaped_pipes():
    """Validates handling uneven column counts (ragged rows) and escaped pipes."""
    md = """| Metric | Value | Notes |
|---|---|---|
| Latency | <10ms | Measured at 99th percentile |
| SLA | 99.99% |
| Syntax | a \\| b | Logical OR pipe |
| Incomplete |
"""
    tables = MarkdownTableParser.parse_tables(md)
    assert len(tables) == 1
    t = tables[0]

    assert t.num_cols == 3
    # Escaped pipe should be unmasked
    assert t.rows[2][1] == "a | b"
    # Incomplete row should be padded with empty strings
    assert len(t.rows[3]) == 3
    assert t.rows[3][0] == "Incomplete"
    assert t.rows[3][1] == ""
    assert t.rows[3][2] == ""


def test_table_to_markdown_and_csv_formatting():
    """Validates round-trip table formatting to clean Markdown and CSV."""
    t = TableData(
        headers=["Device", "IP Address", "Status"],
        rows=[
            ["Router-Core", "192.168.1.1", "Online"],
            ["Switch-Acc", "192.168.1.2", "Degraded"],
        ],
        caption="Network Nodes",
    )

    md_out = t.to_markdown()
    assert "**Table: Network Nodes**" in md_out
    assert "| Device      | IP Address  | Status   |" in md_out
    assert "| Router-Core | 192.168.1.1 | Online   |" in md_out

    csv_out = t.to_csv()
    assert "Device,IP Address,Status" in csv_out
    assert "Router-Core,192.168.1.1,Online" in csv_out


def test_table_cell_authentic_coordinates():
    """Validates that authentic cell coordinates are preserved and never fabricated."""
    cell_with_coords = TableCell(
        content="Optical Loss",
        row_index=1,
        col_index=2,
        coordinates={"x0": 105.5, "y0": 240.0, "x1": 185.0, "y1": 255.0},
    )
    assert cell_with_coords.coordinates is not None
    assert cell_with_coords.coordinates["x0"] == 105.5

    # Markdown parsed cell must have coordinates=None (no fabrication)
    t = TableData(headers=["ColA"], rows=[["Val1"]])
    assert t.cells[0].coordinates is None
    assert t.cells[1].coordinates is None


# ==============================================================================
# 2. Integration with Contextual Document Chunker
# ==============================================================================

def test_table_chunking_parent_child_lineage():
    """Validates that ContextualDocumentChunker generates structured table child chunks."""
    content = """## Page 1
System hardware inventory.

| Component | Serial Number | Status |
|---|---|---|
| Mainboard | MB-9912 | Active |
| PSU | PS-4401 | Verified |
"""
    meta = CanonicalMetadata(source_type="doc.pdf", source_path="/docs/hardware.pdf")
    doc = SemanticDocument(
        schema_version="1.0",
        document_id="222233334444555566667777888899990000aaaabbbbccccddddeeeeffff1111",
        sanitized_content=content,
        document_type="document",
        metadata=meta,
    )

    chunker = ContextualDocumentChunker()
    chunks = chunker.chunk_document(doc)

    # Find Page 1 parent chunk
    p1 = next(c for c in chunks if c.lineage and c.lineage.location and c.lineage.location.page == 1 and "## Page 1" in c.sanitized_content)

    # Find Table child chunk
    table_chunks = [
        c for c in chunks
        if c.lineage and c.lineage.parent_chunk_id == p1.chunk_id and c.sanitized_content.strip().startswith("| Component | Serial Number |")
    ]
    assert len(table_chunks) == 1
    tbl = table_chunks[0]
    assert tbl.lineage.parent_chunk_id == p1.chunk_id
    assert tbl.lineage.location.page == 1
    assert tbl.document_id == doc.document_id


# ==============================================================================
# 3. Knowledge Graph Structural Table & Image Integration
# ==============================================================================

def test_knowledge_graph_table_and_image_nodes_and_relationships():
    """Validates that KnowledgeGraph extractor creates structural table and image nodes."""
    tenant = "tenant-enterprise"
    content = """## Page 1
Network configuration details.

| Port | Protocol | Port Number |
|---|---|---|
| Web | HTTPS | 443 |
| SSH | SSH | 22 |

![Network Topology](images/topology.png)
> **Extracted OCR Text**: Core Gateway Router-East IP: 10.0.0.1
"""
    meta = CanonicalMetadata(source_type="doc.pdf", source_path="/docs/net.pdf")
    doc = SemanticDocument(
        schema_version="1.0",
        document_id="33334444555566667777888899990000aaaabbbbccccddddeeeeffff11112222",
        sanitized_content=content,
        document_type="document",
        metadata=meta,
    )

    chunker = ContextualDocumentChunker()
    chunks = chunker.chunk_document(doc)

    kg = extract(doc, chunks, tenant_id=tenant, extract_structural=True)

    # Verify Table Node
    table_nodes = [n for n in kg.nodes.values() if n.entity_type == "table"]
    assert len(table_nodes) >= 1
    tbl_n = table_nodes[0]
    assert tbl_n.tenant_id == tenant
    assert "headers" in tbl_n.properties
    assert tbl_n.properties["headers"] == ["Port", "Protocol", "Port Number"]
    assert tbl_n.properties["num_rows"] == 3

    # Verify Image Node & OCR property
    image_nodes = [n for n in kg.nodes.values() if n.entity_type == "image"]
    assert len(image_nodes) >= 1
    img_n = image_nodes[0]
    assert img_n.tenant_id == tenant
    assert "ocr_text" in img_n.properties
    assert "Core Gateway Router-East" in img_n.properties["ocr_text"]

    # Verify Structural Relationships
    # (Page)-[:CONTAINS_TABLE]->(Table)
    contains_table_edges = [
        e for e in kg.edges.values()
        if e.relationship_type == "CONTAINS_TABLE" and e.target_id == tbl_n.node_id
    ]
    assert len(contains_table_edges) >= 1

    # (Page)-[:CONTAINS_IMAGE]->(Image)
    contains_image_edges = [
        e for e in kg.edges.values()
        if e.relationship_type == "CONTAINS_IMAGE" and e.target_id == img_n.node_id
    ]
    assert len(contains_image_edges) >= 1


def test_reconciliation_cleans_deleted_table_and_image_nodes():
    """Validates that incremental graph reconciler deletes orphaned table/image nodes."""
    tenant = "tenant-sync"
    store = InMemoryGraphStore()
    reconciler = GraphReconciler(store=store)

    doc_id = "4444555566667777888899990000aaaabbbbccccddddeeeeffff111122223333"

    # Step 1: Ingest document with table and image
    v1_content = """## Page 1
| Key | Value |
|---|---|
| Alpha | 100 |

![Diag](images/diag.png)
> **Extracted OCR Text**: Optical Switch A
"""
    doc_v1 = SemanticDocument(
        schema_version="1.0",
        document_id=doc_id,
        sanitized_content=v1_content,
        document_type="document",
        metadata=CanonicalMetadata(source_type="doc.pdf", source_path="/docs/spec.pdf"),
    )
    chunker = ContextualDocumentChunker()
    chunks_v1 = chunker.chunk_document(doc_v1)

    res1 = reconciler.reconcile_document(doc_v1, chunks_v1, tenant_id=tenant, store=store)
    assert len(res1.diff.inserted_nodes) > 0

    # Verify table node is in store
    all_nodes_v1 = store.get_all_nodes(tenant)
    assert any(n.entity_type == "table" for n in all_nodes_v1)
    assert any(n.entity_type == "image" for n in all_nodes_v1)

    # Step 2: Update document - remove table and image completely
    v2_content = """## Page 1
Plain text description with no tables and no images.
"""
    doc_v2 = SemanticDocument(
        schema_version="1.0",
        document_id=doc_id,
        sanitized_content=v2_content,
        document_type="document",
        metadata=CanonicalMetadata(source_type="doc.pdf", source_path="/docs/spec.pdf"),
    )
    chunks_v2 = chunker.chunk_document(doc_v2)

    res2 = reconciler.reconcile_document(doc_v2, chunks_v2, tenant_id=tenant, store=store)
    assert len(res2.diff.deleted_node_ids) > 0

    # Table and Image nodes must now be removed from store!
    all_nodes_v2 = store.get_all_nodes(tenant)
    assert not any(n.entity_type == "table" for n in all_nodes_v2)
    assert not any(n.entity_type == "image" for n in all_nodes_v2)


# ==============================================================================
# 4. Hybrid Retrieval of Table and OCR Content
# ==============================================================================

def test_hybrid_retrieval_of_table_and_ocr_chunks():
    """Validates that table and OCR child chunks are indexed and searchable via EnterpriseHybridRetriever."""
    from md_generator.retrieval.bm25 import BM25Index
    from md_generator.retrieval.hybrid_retriever import EnterpriseHybridRetriever
    from md_generator.vector.providers.mock import MockEmbeddingProvider
    from md_generator.vector.stores.in_memory import InMemoryVectorStore
    from md_generator.vector.model import EmbeddingRecord, CollectionConfig

    tenant = "tenant-retrieval"
    doc_id = "555566667777888899990000aaaabbbbccccddddeeeeffff1111222233334444"

    content = """## Page 1
Infrastructure specifications.

| Component | Serial Number | Status |
|---|---|---|
| Core Router | CR-8800 | Online |
| Mainboard | MB-9912 | Active |

![Topology](images/topo.png)
> **Extracted OCR Text**: HighSpeed Optical Switch OS-99
"""
    doc = SemanticDocument(
        schema_version="1.0",
        document_id=doc_id,
        sanitized_content=content,
        document_type="document",
        metadata=CanonicalMetadata(source_type="doc.pdf", source_path="/docs/infra.pdf"),
    )

    chunker = ContextualDocumentChunker()
    chunks = chunker.chunk_document(doc)

    # Initialize retriever
    bm25 = BM25Index()
    p384 = MockEmbeddingProvider(dimension=384)
    vstore = InMemoryVectorStore()
    vstore.initialize_collection(CollectionConfig(collection_name="table_col", dimension=384))

    records = []
    for idx, c in enumerate(chunks):
        bm25.add_document(c.chunk_id, c.sanitized_content, tenant_id=tenant, metadata={"document_id": doc_id})
        vec = p384.embed_texts([c.sanitized_content])[0]
        records.append(
            EmbeddingRecord(
                embedding_id=f"emb_{idx}",
                chunk_id=c.chunk_id,
                document_id=doc_id,
                vector=vec,
                dimension=384,
                provider_name="mock",
                model_name="mock",
                model_version="1.0",
                sanitized_content=c.sanitized_content,
                semantic_key=f"k_{idx}",
                tenant_id=tenant,
                payload={"document_id": doc_id},
            )
        )
    vstore.upsert_records(records, tenant_id=tenant)

    retriever = EnterpriseHybridRetriever(
        vector_store=vstore,
        embedding_provider=p384,
        tenant_id=tenant,
        bm25_index=bm25,
        top_k=5,
    )

    # Query 1: Search for table content
    table_results = retriever.retrieve("Mainboard MB-9912")
    assert len(table_results) > 0
    top_tbl = table_results[0]
    assert "MB-9912" in top_tbl.content
    assert "| Component | Serial Number | Status |" in top_tbl.content

    # Query 2: Search for OCR text
    ocr_results = retriever.retrieve("HighSpeed Optical Switch OS-99")
    assert len(ocr_results) > 0
    top_ocr = ocr_results[0]
    assert "Optical Switch OS-99" in top_ocr.content


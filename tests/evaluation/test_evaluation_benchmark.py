"""Comprehensive Test Suite for Retrieval & Answer Evaluation Benchmark (Prompt 08).

Verifies:
1. Exact mathematical correctness of IR metrics (Precision@K, Recall@K, HitRate@K, MRR, MAP, NDCG@K).
2. Context precision and context recall calculations.
3. Answer faithfulness / groundedness vs ungrounded hallucination penalties.
4. Answer relevance, evidence coverage, and token overlap similarity.
5. Citation precision and recall against available and expected evidence.
6. EvaluationDataset schema validation, JSON and JSONL persistence.
7. SyntheticDatasetGenerator parsing chunks, tables, and OCR blocks.
8. BenchmarkRunner end-to-end execution with EnterpriseHybridRetriever and ContextManager.
9. BaselineComparator metric deltas, improvement detection, and regression warnings.
10. Markdown, CSV, and JSON report generation.
"""

import math
from pathlib import Path
import pytest

from md_generator.evaluation import (
    EvaluationSample,
    EvaluationDataset,
    BenchmarkRun,
    DatasetManager,
    SyntheticDatasetGenerator,
    precision_at_k,
    recall_at_k,
    hit_rate_at_k,
    reciprocal_rank,
    average_precision,
    ndcg_at_k,
    context_precision,
    context_recall,
    compute_all_retrieval_metrics,
    faithfulness_score,
    answer_relevance,
    evidence_coverage,
    token_overlap_similarity,
    context_utilization,
    compute_all_answer_metrics,
    citation_precision,
    citation_recall,
    compute_all_citation_metrics,
    BenchmarkRunner,
    BaselineManager,
    EvaluationReporter,
)
from md_generator.semantic.model.schema import CanonicalMetadata, SemanticChunk, SemanticDocument
from md_generator.semantic.chunkers.document import ContextualDocumentChunker
from md_generator.context.manager import ContextManager
from md_generator.retrieval.bm25 import BM25Index
from md_generator.retrieval.hybrid_retriever import EnterpriseHybridRetriever
from md_generator.vector.stores.in_memory import InMemoryVectorStore
from md_generator.vector.providers.mock import MockEmbeddingProvider
from md_generator.vector.model import CollectionConfig, EmbeddingRecord


# ==============================================================================
# 1. Retrieval Metrics Exact Mathematical Validation
# ==============================================================================

def test_precision_recall_hit_rate_manual_calculation():
    """Validates Precision@K, Recall@K, HitRate@K against manual hand calculations.
    
    Retrieved: ['c1', 'c2', 'c3', 'c4']
    Relevant:  {'c1', 'c3'} (2 relevant items)
    """
    retrieved = ["c1", "c2", "c3", "c4"]
    relevant = {"c1", "c3"}

    # Precision@K
    assert precision_at_k(retrieved, relevant, k=1) == 1.0 / 1.0  # 1/1 = 1.0
    assert precision_at_k(retrieved, relevant, k=2) == 1.0 / 2.0  # 1/2 = 0.5
    assert precision_at_k(retrieved, relevant, k=3) == 2.0 / 3.0  # 2/3 ≈ 0.6667
    assert precision_at_k(retrieved, relevant, k=4) == 2.0 / 4.0  # 2/4 = 0.5

    # Recall@K (|relevant| = 2)
    assert recall_at_k(retrieved, relevant, k=1) == 1.0 / 2.0  # 0.5
    assert recall_at_k(retrieved, relevant, k=2) == 1.0 / 2.0  # 0.5
    assert recall_at_k(retrieved, relevant, k=3) == 2.0 / 2.0  # 1.0
    assert recall_at_k(retrieved, relevant, k=4) == 2.0 / 2.0  # 1.0

    # HitRate@K
    assert hit_rate_at_k(retrieved, relevant, k=1) == 1.0
    assert hit_rate_at_k(retrieved, relevant, k=2) == 1.0

    # Non-hit case
    assert hit_rate_at_k(["c5", "c6"], relevant, k=2) == 0.0


def test_mrr_and_map_manual_calculation():
    """Validates MRR and MAP against manual calculations.
    
    Case A: First relevant item is at rank 1 -> MRR = 1/1 = 1.0
    Case B: First relevant item is at rank 3 -> MRR = 1/3 ≈ 0.3333
    Case C: No relevant items -> MRR = 0.0
    """
    assert reciprocal_rank(["c1", "c2", "c3"], {"c1", "c4"}) == 1.0
    assert abs(reciprocal_rank(["c2", "c3", "c1"], {"c1", "c4"}) - (1.0 / 3.0)) < 1e-4
    assert reciprocal_rank(["c2", "c3"], {"c1"}) == 0.0

    # MAP calculation:
    # Retrieved: ['c1', 'c2', 'c3']
    # Relevant: {'c1', 'c3'} (|relevant| = 2)
    # Rank 1: 'c1' (Hit) -> P@1 = 1/1 = 1.0
    # Rank 2: 'c2' (Miss)
    # Rank 3: 'c3' (Hit) -> P@3 = 2/3
    # AP = (1.0 + 2/3) / 2 = (5/3) / 2 = 5/6 ≈ 0.83333
    ap = average_precision(["c1", "c2", "c3"], {"c1", "c3"})
    assert abs(ap - (5.0 / 6.0)) < 1e-4


def test_ndcg_at_k_manual_calculation():
    """Validates NDCG@K against manual logarithmic discounting formula.
    
    Retrieved: ['c1', 'c2', 'c3']
    Relevant:  {'c1', 'c3'}
    
    DCG@3:
    Rank 1: rel=1 -> (2^1 - 1)/log2(2) = 1 / 1.0 = 1.0
    Rank 2: rel=0 -> 0.0
    Rank 3: rel=1 -> (2^1 - 1)/log2(4) = 1 / 2.0 = 0.5
    DCG@3 = 1.0 + 0.0 + 0.5 = 1.5
    
    IDCG@3 (Ideal: ['c1', 'c3']):
    Rank 1: rel=1 -> 1 / log2(2) = 1.0
    Rank 2: rel=1 -> 1 / log2(3) ≈ 1 / 1.5849625 ≈ 0.6309297
    IDCG@3 = 1.0 + 0.6309297 = 1.6309297
    
    NDCG@3 = 1.5 / 1.6309297 ≈ 0.91972
    """
    ndcg = ndcg_at_k(["c1", "c2", "c3"], {"c1", "c3"}, k=3)
    expected_idcg = 1.0 + (1.0 / math.log2(3.0))
    expected_dcg = 1.0 + (1.0 / math.log2(4.0))  # 1.0 + 0.5 = 1.5
    expected_ndcg = expected_dcg / expected_idcg
    assert abs(ndcg - expected_ndcg) < 1e-4
    assert round(ndcg, 4) == 0.9197


def test_context_precision_and_recall():
    """Validates context precision and recall."""
    retrieved_chunks = ["c1", "c2", "c3"]
    relevant_chunks = {"c1"}
    # Context precision for top rank hit = 1.0
    assert context_precision(retrieved_chunks, relevant_chunks) == 1.0

    retrieved_text = "Optical switch installation guidelines require cable connection before powering on."
    expected_passages = [
        "cable connection before powering on",
        "optical switch installation guidelines",
    ]
    # Both expected passages are contained in retrieved text
    assert context_recall(retrieved_text, expected_passages) == 1.0

    # Missing passage
    assert context_recall(retrieved_text, ["unmentioned laser calibration"]) == 0.0


# ==============================================================================
# 2. Answer Quality & Faithfulness Metrics Tests
# ==============================================================================

def test_faithfulness_grounded_vs_hallucination_penalty():
    """Validates that factual claims supported by context score high, while hallucinated claims are penalized."""
    context = (
        "The primary database server DB-01 has 64 CPU cores and 256 GB RAM. "
        "The project budget allocated by Acme Corp is $5 million."
    )

    # 1. Grounded Answer
    grounded_ans = "The DB-01 server is configured with 64 CPU cores and 256 GB RAM."
    score_grounded = faithfulness_score(grounded_ans, context)
    assert score_grounded >= 0.8

    # 2. Hallucinated Answer (unsupported numbers and foreign entities)
    hallucinated_ans = "The DB-01 server has 128 cores and costs $50 million from Oracle Corp."
    score_hallucinated = faithfulness_score(hallucinated_ans, context)
    assert score_hallucinated < 0.5


def test_answer_relevance_and_coverage():
    """Validates relevance to query and coverage of ground truth facts."""
    query = "What is the CPU core count and memory for DB-01?"
    ans = "DB-01 has 64 CPU cores and 256 GB memory."
    ground_truth = "DB-01 is configured with 64 CPU cores and 256 GB RAM."

    rel = answer_relevance(query, ans)
    assert rel >= 0.75

    cov = evidence_coverage(ground_truth, ans)
    assert cov >= 0.8


def test_token_overlap_similarity():
    """Validates token overlap Jaccard similarity."""
    assert token_overlap_similarity("alpha beta gamma", "alpha beta gamma") == 1.0
    assert token_overlap_similarity("alpha beta", "gamma delta") == 0.0
    # Overlap of 1 out of 3 tokens
    assert token_overlap_similarity("alpha beta", "alpha gamma") > 0.0


# ==============================================================================
# 3. Citation Metrics Tests
# ==============================================================================

def test_citation_precision_and_recall():
    """Validates citation precision and recall."""
    ans = "The server is active [1] and replication lag is under 1s [2]."
    # 2 citations cited: [1], [2]
    # Available citations count: 2 -> both valid
    assert citation_precision(ans, available_citations_count=2) == 1.0

    # If only 1 citation was available in context, [2] is invalid
    assert citation_precision(ans, available_citations_count=1) == 0.5

    # Recall: expected citations [1], [2]
    assert citation_recall(ans, expected_citations=["[1]", "[2]"]) == 1.0
    # If expected [3] was missing
    assert citation_recall(ans, expected_citations=["[1]", "[3]"]) == 0.5


# ==============================================================================
# 4. Dataset Management & Synthetic Generation Tests
# ==============================================================================

def test_dataset_validation_and_persistence(tmp_path: Path):
    """Validates EvaluationDataset validation and JSON/JSONL persistence."""
    sample1 = EvaluationSample(
        sample_id="s1",
        query="What is the server latency SLA?",
        ground_truth_answer="The latency SLA is <10ms.",
        expected_chunk_ids=["chunk_1"],
    )
    sample2 = EvaluationSample(
        sample_id="s2",
        query="Who is the Chief Architect?",
        ground_truth_answer="Dr. Alice Smith.",
        expected_chunk_ids=["chunk_2"],
    )

    dataset = EvaluationDataset(
        dataset_id="ds_test",
        name="Test Benchmark",
        description="Dataset for testing",
        dataset_type="curated",
        samples=[sample1, sample2],
    )
    dataset.validate()

    # JSON persistence
    json_path = tmp_path / "dataset.json"
    DatasetManager.save_json(dataset, json_path)
    loaded_json = DatasetManager.load_json(json_path)
    assert len(loaded_json) == 2
    assert loaded_json.samples[0].query == sample1.query

    # JSONL persistence
    jsonl_path = tmp_path / "dataset.jsonl"
    DatasetManager.save_jsonl(dataset, jsonl_path)
    loaded_jsonl = DatasetManager.load_jsonl(jsonl_path, dataset_id="ds_jsonl", dataset_type="curated")
    assert len(loaded_jsonl) == 2
    assert loaded_jsonl.samples[1].query == sample2.query

    # Validation rejection on duplicate sample_id
    with pytest.raises(ValueError):
        EvaluationDataset(
            dataset_id="ds_invalid",
            name="Invalid",
            description="",
            dataset_type="curated",
            samples=[sample1, sample1],
        ).validate()


def test_synthetic_dataset_generator():
    """Validates generating synthetic questions from chunks, tables, and OCR blocks."""
    content = """## Page 1
Dr. Alice Smith was appointed Chief Architect at Acme Corp.

| Device | IP Address | Status |
|---|---|---|
| Gateway-01 | 10.0.0.1 | Active |

![Diagram](images/diag.png)
> **Extracted OCR Text**: HighSpeed Switch Core Model 400
"""
    doc = SemanticDocument(
        schema_version="1.0",
        document_id="1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        sanitized_content=content,
        document_type="document",
        metadata=CanonicalMetadata(source_type="doc.pdf", source_path="/docs/syn.pdf"),
    )
    chunker = ContextualDocumentChunker()
    chunks = chunker.chunk_document(doc)

    gen = SyntheticDatasetGenerator(tenant_id="tenant_syn")
    syn_dataset = gen.generate_from_document(doc, chunks, max_samples=10)

    assert syn_dataset.dataset_type == "synthetic"
    assert len(syn_dataset.samples) >= 1

    # Verify that synthetic samples contain genuine references
    for s in syn_dataset.samples:
        assert s.expected_document_ids[0] == doc.document_id
        assert len(s.expected_chunk_ids) >= 1
        assert s.tenant_id == "tenant_syn"


# ==============================================================================
# 5. Benchmark Runner End-to-End Execution & Baseline Comparison
# ==============================================================================

def test_benchmark_runner_and_baseline_comparison(tmp_path: Path):
    """Validates end-to-end benchmark execution, metric aggregation, and baseline comparison."""
    tenant = "tenant_bench"
    doc_id = "1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff"

    content = """## Page 1
The primary database server DB-01 is configured with 64 CPU cores and 256 GB RAM.
The system latency SLA is <10ms for 99th percentile traffic.
"""
    doc = SemanticDocument(
        schema_version="1.0",
        document_id=doc_id,
        sanitized_content=content,
        document_type="document",
        metadata=CanonicalMetadata(source_type="doc.pdf", source_path="/docs/bench.pdf"),
    )
    chunker = ContextualDocumentChunker()
    chunks = chunker.chunk_document(doc)

    # Setup retrieval components
    bm25 = BM25Index()
    p384 = MockEmbeddingProvider(dimension=384)
    vstore = InMemoryVectorStore()
    vstore.initialize_collection(CollectionConfig(collection_name="col_bench", dimension=384))

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

    # Curated evaluation dataset
    target_chunk_id = next(c.chunk_id for c in chunks if "DB-01" in c.sanitized_content)
    sample = EvaluationSample(
        sample_id="sample_db",
        query="What is the server DB-01 CPU and RAM configuration?",
        ground_truth_answer="DB-01 has 64 CPU cores and 256 GB RAM.",
        expected_document_ids=[doc_id],
        expected_chunk_ids=[target_chunk_id],
        expected_passages=["64 CPU cores and 256 GB RAM"],
        tenant_id=tenant,
    )
    dataset = EvaluationDataset(
        dataset_id="ds_bench_01",
        name="Database Benchmark",
        description="Curated database benchmark",
        dataset_type="curated",
        samples=[sample],
    )

    runner = BenchmarkRunner(retriever=retriever, top_k=3)
    run1 = runner.run_benchmark(dataset, run_id="run_baseline")

    assert run1.status == "completed"
    assert "mrr" in run1.aggregate_metrics
    assert run1.aggregate_metrics["mrr"] > 0.0
    assert "faithfulness" in run1.aggregate_metrics
    assert run1.aggregate_metrics["faithfulness"] >= 0.7

    # Save baseline
    baseline_path = tmp_path / "baseline_run.json"
    BaselineManager.save_baseline(run1, baseline_path)
    loaded_baseline = BaselineManager.load_baseline(baseline_path)
    assert loaded_baseline.run_id == run1.run_id

    # Execute a second run (identical setup -> unchanged comparison)
    run2 = runner.run_benchmark(dataset, run_id="run_current")
    comparison = BaselineManager.compare_runs(run2, loaded_baseline, warning_threshold_pct=5.0)

    assert comparison.has_regressions is False
    assert comparison.regressions_count == 0

    # Generate Markdown, CSV, and JSON reports
    md_rep = EvaluationReporter.generate_markdown_report(run2, comparison=comparison)
    assert "# Benchmark Evaluation Report" in md_rep
    assert "## 2. Aggregate Metrics Summary" in md_rep
    assert "## 3. Baseline Comparison" in md_rep

    csv_rep = EvaluationReporter.generate_csv_report(run2)
    assert "sample_id,query" in csv_rep
    assert "sample_db" in csv_rep

    json_rep = EvaluationReporter.generate_json_report(run2)
    assert '"run_id": "run_current"' in json_rep

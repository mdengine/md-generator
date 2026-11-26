from __future__ import annotations

"""Metrics package for retrieval, answer quality, and citation evaluation."""

from md_generator.evaluation.metrics.retrieval import (
    precision_at_k,
    recall_at_k,
    hit_rate_at_k,
    reciprocal_rank,
    average_precision,
    ndcg_at_k,
    context_precision,
    context_recall,
    compute_all_retrieval_metrics,
)
from md_generator.evaluation.metrics.answer import (
    faithfulness_score,
    answer_relevance,
    evidence_coverage,
    token_overlap_similarity,
    context_utilization,
    compute_all_answer_metrics,
)
from md_generator.evaluation.metrics.citation import (
    extract_citation_indices,
    citation_precision,
    citation_recall,
    compute_all_citation_metrics,
)

__all__ = [
    "precision_at_k",
    "recall_at_k",
    "hit_rate_at_k",
    "reciprocal_rank",
    "average_precision",
    "ndcg_at_k",
    "context_precision",
    "context_recall",
    "compute_all_retrieval_metrics",
    "faithfulness_score",
    "answer_relevance",
    "evidence_coverage",
    "token_overlap_similarity",
    "context_utilization",
    "compute_all_answer_metrics",
    "extract_citation_indices",
    "citation_precision",
    "citation_recall",
    "compute_all_citation_metrics",
]

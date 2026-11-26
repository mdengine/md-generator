from __future__ import annotations

"""Evaluation and Benchmark Engine for md_generator."""

from md_generator.evaluation.models import (
    EvaluationSample,
    EvaluationDataset,
    SampleEvaluationResult,
    BenchmarkRun,
)
from md_generator.evaluation.dataset import (
    DatasetManager,
    SyntheticDatasetGenerator,
)
from md_generator.evaluation.metrics import (
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
)
from md_generator.evaluation.runner import BenchmarkRunner
from md_generator.evaluation.baseline import (
    MetricDelta,
    RunComparisonResult,
    BaselineManager,
)
from md_generator.evaluation.report import EvaluationReporter

__all__ = [
    "EvaluationSample",
    "EvaluationDataset",
    "SampleEvaluationResult",
    "BenchmarkRun",
    "DatasetManager",
    "SyntheticDatasetGenerator",
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
    "citation_precision",
    "citation_recall",
    "compute_all_citation_metrics",
    "BenchmarkRunner",
    "MetricDelta",
    "RunComparisonResult",
    "BaselineManager",
    "EvaluationReporter",
]

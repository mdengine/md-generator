from __future__ import annotations

"""Evaluation Framework Data Models & Schemas.

Phase 2F/Prompt 08 Implementation:
- EvaluationSample: represents a single test case (query, ground truth, expected chunks/passages/citations).
- EvaluationDataset: collection of samples, clearly labeled as 'curated' or 'synthetic'.
- SampleEvaluationResult: individual evaluation metrics for retrieval, answer quality, and citations.
- BenchmarkRun: aggregate run configuration, execution stats, and summary metrics.
- RunComparisonResult: metric-by-metric delta against a baseline run.
"""

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import time
from typing import Any, Dict, List, Literal, Optional, Sequence, Set, Union


@dataclass
class EvaluationSample:
    """Represents a single query evaluation instance with ground truth evidence."""
    sample_id: str
    query: str
    ground_truth_answer: Optional[str] = None
    expected_document_ids: List[str] = field(default_factory=list)
    expected_chunk_ids: List[str] = field(default_factory=list)
    expected_passages: List[str] = field(default_factory=list)
    expected_citations: List[str] = field(default_factory=list)
    query_type: str = "factual"  # "factual", "comparative", "multi_hop", "conversational"
    tenant_id: str = "default_tenant"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.sample_id:
            raise ValueError("sample_id must be a non-empty string.")
        if not self.query or not self.query.strip():
            raise ValueError(f"Sample '{self.sample_id}': query cannot be empty.")
        if not self.tenant_id or not self.tenant_id.strip():
            raise ValueError(f"Sample '{self.sample_id}': tenant_id cannot be empty.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "query": self.query,
            "ground_truth_answer": self.ground_truth_answer,
            "expected_document_ids": list(self.expected_document_ids),
            "expected_chunk_ids": list(self.expected_chunk_ids),
            "expected_passages": list(self.expected_passages),
            "expected_citations": list(self.expected_citations),
            "query_type": self.query_type,
            "tenant_id": self.tenant_id,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvaluationSample:
        sample = cls(
            sample_id=data.get("sample_id", f"sample_{hashlib.sha256(data.get('query', '').encode('utf-8')).hexdigest()[:12]}"),
            query=data.get("query", ""),
            ground_truth_answer=data.get("ground_truth_answer"),
            expected_document_ids=data.get("expected_document_ids", []),
            expected_chunk_ids=data.get("expected_chunk_ids", []),
            expected_passages=data.get("expected_passages", []),
            expected_citations=data.get("expected_citations", []),
            query_type=data.get("query_type", "factual"),
            tenant_id=data.get("tenant_id", "default_tenant"),
            metadata=data.get("metadata", {}),
        )
        sample.validate()
        return sample


@dataclass
class EvaluationDataset:
    """Container for a collection of evaluation samples."""
    dataset_id: str
    name: str
    description: str
    dataset_type: Literal["curated", "synthetic"]  # Mandatory distinction!
    samples: List[EvaluationSample] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.dataset_id:
            raise ValueError("dataset_id cannot be empty.")
        if not self.name:
            raise ValueError("dataset name cannot be empty.")
        if self.dataset_type not in ("curated", "synthetic"):
            raise ValueError("dataset_type must be either 'curated' or 'synthetic'.")
        seen_ids: Set[str] = set()
        for s in self.samples:
            s.validate()
            if s.sample_id in seen_ids:
                raise ValueError(f"Duplicate sample_id found: '{s.sample_id}'.")
            seen_ids.add(s.sample_id)

    def __len__(self) -> int:
        return len(self.samples)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "name": self.name,
            "description": self.description,
            "dataset_type": self.dataset_type,
            "created_at": self.created_at,
            "samples_count": len(self.samples),
            "samples": [s.to_dict() for s in self.samples],
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvaluationDataset:
        raw_samples = data.get("samples", [])
        samples = [EvaluationSample.from_dict(s) for s in raw_samples]
        ds = cls(
            dataset_id=data.get("dataset_id", "dataset_default"),
            name=data.get("name", "Evaluation Dataset"),
            description=data.get("description", ""),
            dataset_type=data.get("dataset_type", "curated"),
            samples=samples,
            created_at=data.get("created_at", time.time()),
            metadata=data.get("metadata", {}),
        )
        ds.validate()
        return ds


@dataclass
class SampleEvaluationResult:
    """Individual per-sample benchmark evaluation outcome."""
    sample_id: str
    query: str
    retrieved_chunk_ids: List[str]
    retrieved_documents: List[str]
    generated_answer: str
    citations: List[str]
    retrieval_metrics: Dict[str, float] = field(default_factory=dict)
    answer_metrics: Dict[str, float] = field(default_factory=dict)
    citation_metrics: Dict[str, float] = field(default_factory=dict)
    latency_ms: float = 0.0
    token_usage: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "query": self.query,
            "retrieved_chunk_ids": list(self.retrieved_chunk_ids),
            "retrieved_documents": list(self.retrieved_documents),
            "generated_answer": self.generated_answer,
            "citations": list(self.citations),
            "retrieval_metrics": dict(self.retrieval_metrics),
            "answer_metrics": dict(self.answer_metrics),
            "citation_metrics": dict(self.citation_metrics),
            "latency_ms": self.latency_ms,
            "token_usage": dict(self.token_usage),
            "errors": list(self.errors),
        }


@dataclass
class BenchmarkRun:
    """Aggregated outcome of an entire benchmark evaluation run."""
    run_id: str
    dataset_id: str
    dataset_type: str
    timestamp: float
    configuration: Dict[str, Any]
    aggregate_metrics: Dict[str, float]
    sample_results: List[SampleEvaluationResult] = field(default_factory=list)
    duration_seconds: float = 0.0
    status: str = "completed"  # "completed", "failed", "partial"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "dataset_id": self.dataset_id,
            "dataset_type": self.dataset_type,
            "timestamp": self.timestamp,
            "duration_seconds": self.duration_seconds,
            "status": self.status,
            "configuration": dict(self.configuration),
            "aggregate_metrics": dict(self.aggregate_metrics),
            "total_samples": len(self.sample_results),
            "sample_results": [s.to_dict() for s in self.sample_results],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BenchmarkRun:
        raw_samples = data.get("sample_results", [])
        sample_results = [
            SampleEvaluationResult(
                sample_id=s.get("sample_id", ""),
                query=s.get("query", ""),
                retrieved_chunk_ids=s.get("retrieved_chunk_ids", []),
                retrieved_documents=s.get("retrieved_documents", []),
                generated_answer=s.get("generated_answer", ""),
                citations=s.get("citations", []),
                retrieval_metrics=s.get("retrieval_metrics", {}),
                answer_metrics=s.get("answer_metrics", {}),
                citation_metrics=s.get("citation_metrics", {}),
                latency_ms=s.get("latency_ms", 0.0),
                token_usage=s.get("token_usage", {}),
                errors=s.get("errors", []),
            )
            for s in raw_samples
        ]
        return cls(
            run_id=data.get("run_id", ""),
            dataset_id=data.get("dataset_id", ""),
            dataset_type=data.get("dataset_type", "curated"),
            timestamp=data.get("timestamp", 0.0),
            configuration=data.get("configuration", {}),
            aggregate_metrics=data.get("aggregate_metrics", {}),
            sample_results=sample_results,
            duration_seconds=data.get("duration_seconds", 0.0),
            status=data.get("status", "completed"),
        )

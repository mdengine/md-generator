from __future__ import annotations

"""Benchmark Execution Runner.

Phase 2F/Prompt 08 Implementation:
- BenchmarkRunner: orchestrates evaluation of an EvaluationDataset against
  EnterpriseHybridRetriever, ContextManager, and ChatManager / ExtractiveChatProvider.
- Measures retrieval accuracy (P@K, R@K, MRR, NDCG, ContextPrecision, ContextRecall).
- Measures answer faithfulness, relevance, evidence coverage, and citation metrics.
- Computes aggregate statistical metrics (mean across all samples).
- Records execution time and token usage with complete error isolation.
"""

from dataclasses import asdict
import statistics
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

from md_generator.chat.manager import ChatManager
from md_generator.chat.models import ExecutionMode
from md_generator.chat.providers.base import BaseChatProvider
from md_generator.chat.providers.extractive import ExtractiveChatProvider
from md_generator.context.manager import ContextManager
from md_generator.evaluation.metrics.answer import compute_all_answer_metrics
from md_generator.evaluation.metrics.citation import compute_all_citation_metrics
from md_generator.evaluation.metrics.retrieval import compute_all_retrieval_metrics
from md_generator.evaluation.models import (
    BenchmarkRun,
    EvaluationDataset,
    EvaluationSample,
    SampleEvaluationResult,
)
from md_generator.retrieval.hybrid_retriever import EnterpriseHybridRetriever


class BenchmarkRunner:
    """Executes automated evaluation runs across retrieval and answer generation."""

    def __init__(
        self,
        retriever: Optional[EnterpriseHybridRetriever] = None,
        context_manager: Optional[ContextManager] = None,
        chat_provider: Optional[BaseChatProvider] = None,
        chat_manager: Optional[ChatManager] = None,
        top_k: int = 5,
    ) -> None:
        self.retriever = retriever
        self.context_manager = context_manager or ContextManager()
        self.chat_provider = chat_provider or ExtractiveChatProvider()
        self.chat_manager = chat_manager
        self.top_k = top_k

    def run_benchmark(
        self,
        dataset: EvaluationDataset,
        run_id: Optional[str] = None,
        k_values: Sequence[int] = (1, 3, 5),
    ) -> BenchmarkRun:
        """Executes full benchmark evaluation across all samples in the dataset."""
        dataset.validate()
        start_time = time.perf_counter()
        actual_run_id = run_id or f"run_{dataset.dataset_id}_{int(time.time())}"

        sample_results: List[SampleEvaluationResult] = []

        for sample in dataset.samples:
            sample_start = time.perf_counter()
            retrieved_chunk_ids: List[str] = []
            retrieved_docs: List[str] = []
            retrieved_chunks_raw: List[Dict[str, Any]] = []
            retrieved_context_text = ""
            errors: List[str] = []
            generated_answer = ""
            available_citations_count = 0
            token_usage: Dict[str, int] = {}

            # 1. Execute Retrieval Stage
            if self.retriever is not None:
                try:
                    # Verify tenant boundary compatibility if retriever is tenant-scoped
                    retriever_tenant = getattr(self.retriever, "clean_tenant", getattr(self.retriever, "tenant_id", None))
                    if retriever_tenant and retriever_tenant != sample.tenant_id:
                        raise ValueError(
                            f"Tenant boundary mismatch: retriever is bound to '{retriever_tenant}' but sample belongs to '{sample.tenant_id}'."
                        )

                    k_target = max(k_values) if k_values else self.top_k
                    candidates = self.retriever.retrieve(
                        query=sample.query,
                        top_k=k_target,
                    )
                    for cand in candidates:
                        retrieved_chunk_ids.append(cand.chunk_id)
                        retrieved_chunks_raw.append(cand)
                        doc_id = cand.metadata.get("document_id")
                        if doc_id and doc_id not in retrieved_docs:
                            retrieved_docs.append(doc_id)
                except Exception as e:
                    errors.append(f"Retrieval error: {str(e)}")

            # 2. Execute Context Assembly Stage
            if retrieved_chunks_raw:
                try:
                    assembled = self.context_manager.assemble_context(
                        retrieved_items=retrieved_chunks_raw,
                        tenant_id=sample.tenant_id,
                    )
                    retrieved_context_text = assembled.context_text
                    available_citations_count = len(assembled.citations)

                    # 3. Execute Answer Generation Stage
                    ans_text, usage = self.chat_provider.generate_response(
                        query=sample.query,
                        context=assembled,
                        history=[],
                    )
                    generated_answer = ans_text
                    token_usage = usage
                except Exception as e:
                    errors.append(f"Answer synthesis error: {str(e)}")

            sample_latency = (time.perf_counter() - sample_start) * 1000

            # 4. Compute Metrics
            retrieval_metrics = compute_all_retrieval_metrics(
                retrieved_chunk_ids=retrieved_chunk_ids,
                expected_chunk_ids=sample.expected_chunk_ids,
                k_values=tuple(k_values),
                retrieved_context_text=retrieved_context_text,
                expected_passages=sample.expected_passages,
            )

            answer_metrics = compute_all_answer_metrics(
                query=sample.query,
                generated_answer=generated_answer,
                retrieved_context=retrieved_context_text,
                ground_truth_answer=sample.ground_truth_answer,
            )

            citation_metrics = compute_all_citation_metrics(
                generated_answer=generated_answer,
                available_citations_count=available_citations_count,
                expected_citations=sample.expected_citations,
            )

            sample_results.append(
                SampleEvaluationResult(
                    sample_id=sample.sample_id,
                    query=sample.query,
                    retrieved_chunk_ids=retrieved_chunk_ids,
                    retrieved_documents=retrieved_docs,
                    generated_answer=generated_answer,
                    citations=[f"[{i}]" for i in range(1, available_citations_count + 1)],
                    retrieval_metrics=retrieval_metrics,
                    answer_metrics=answer_metrics,
                    citation_metrics=citation_metrics,
                    latency_ms=sample_latency,
                    token_usage=token_usage,
                    errors=errors,
                )
            )

        duration = time.perf_counter() - start_time

        # 5. Compute Aggregate Metrics (Mean across all samples)
        aggregate_metrics = self._compute_aggregate_metrics(sample_results)

        return BenchmarkRun(
            run_id=actual_run_id,
            dataset_id=dataset.dataset_id,
            dataset_type=dataset.dataset_type,
            timestamp=time.time(),
            configuration={
                "top_k": self.top_k,
                "k_values": list(k_values),
                "chat_provider": getattr(self.chat_provider, "__class__", type(self.chat_provider)).__name__,
            },
            aggregate_metrics=aggregate_metrics,
            sample_results=sample_results,
            duration_seconds=duration,
            status="completed" if not any(s.errors for s in sample_results) else "partial",
        )

    @staticmethod
    def _compute_aggregate_metrics(samples: List[SampleEvaluationResult]) -> Dict[str, float]:
        """Calculates arithmetic mean for each metric across all evaluated samples."""
        if not samples:
            return {}

        metric_pools: Dict[str, List[float]] = {}

        for s in samples:
            # Combine all metrics
            all_m = {**s.retrieval_metrics, **s.answer_metrics, **s.citation_metrics}
            for k, val in all_m.items():
                if k not in metric_pools:
                    metric_pools[k] = []
                metric_pools[k].append(val)

        aggregates: Dict[str, float] = {}
        for m_name, vals in metric_pools.items():
            aggregates[m_name] = round(statistics.mean(vals), 4) if vals else 0.0

        # Also aggregate latency
        latencies = [s.latency_ms for s in samples]
        aggregates["mean_latency_ms"] = round(statistics.mean(latencies), 2) if latencies else 0.0

        return aggregates

from __future__ import annotations

"""Information Retrieval Metrics (Pure Python / Deterministic).

Phase 2F/Prompt 08 Implementation:
- Precision@K: fraction of retrieved items at rank K that are relevant.
- Recall@K: fraction of total relevant items retrieved at rank K.
- HitRate@K: 1.0 if at least one relevant item is retrieved in top K, else 0.0.
- Mean Reciprocal Rank (MRR): 1 / rank of first relevant item.
- Mean Average Precision (MAP): mean of precision values calculated at each relevant hit.
- Normalized Discounted Cumulative Gain (NDCG@K): graded ranking quality relative to ideal ordering.
- ContextPrecision: rank-weighted relevance of retrieved passages.
- ContextRecall: coverage of expected evidence entities/tokens in retrieved text.
"""

import math
from typing import Dict, List, Optional, Sequence, Set, Union


def precision_at_k(retrieved: Sequence[str], relevant: Set[str], k: int) -> float:
    """Calculates Precision@K = |retrieved[:k] ∩ relevant| / k."""
    if k <= 0:
        return 0.0
    if not retrieved:
        return 0.0
    cutoff = list(retrieved)[:k]
    hits = sum(1 for item in cutoff if item in relevant)
    return hits / k


def recall_at_k(retrieved: Sequence[str], relevant: Set[str], k: int) -> float:
    """Calculates Recall@K = |retrieved[:k] ∩ relevant| / |relevant|."""
    if not relevant:
        return 1.0 if not retrieved else 0.0
    if k <= 0 or not retrieved:
        return 0.0
    cutoff = list(retrieved)[:k]
    hits = sum(1 for item in cutoff if item in relevant)
    return hits / len(relevant)


def hit_rate_at_k(retrieved: Sequence[str], relevant: Set[str], k: int) -> float:
    """Calculates HitRate@K (Success@K) = 1.0 if any relevant in retrieved[:k] else 0.0."""
    if k <= 0 or not retrieved or not relevant:
        return 0.0
    cutoff = list(retrieved)[:k]
    return 1.0 if any(item in relevant for item in cutoff) else 0.0


def reciprocal_rank(retrieved: Sequence[str], relevant: Set[str]) -> float:
    """Calculates Reciprocal Rank (RR) = 1 / rank of first relevant item."""
    if not retrieved or not relevant:
        return 0.0
    for rank, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1.0 / rank
    return 0.0


def average_precision(retrieved: Sequence[str], relevant: Set[str]) -> float:
    """Calculates Average Precision (AP) for a single query."""
    if not relevant:
        return 0.0
    if not retrieved:
        return 0.0

    hits = 0
    sum_precisions = 0.0
    for rank, item in enumerate(retrieved, start=1):
        if item in relevant:
            hits += 1
            sum_precisions += hits / rank

    return sum_precisions / len(relevant)


def ndcg_at_k(retrieved: Sequence[str], relevant: Set[str], k: int) -> float:
    """Calculates Normalized Discounted Cumulative Gain at K (NDCG@K)."""
    if k <= 0:
        return 0.0
    if not relevant:
        return 1.0 if not retrieved else 0.0

    # Binary DCG
    dcg = 0.0
    cutoff = list(retrieved)[:k]
    for i, item in enumerate(cutoff, start=1):
        rel = 1.0 if item in relevant else 0.0
        if rel > 0:
            dcg += (2.0**rel - 1.0) / math.log2(i + 1.0)

    # Ideal DCG
    idcg = 0.0
    ideal_hits = min(k, len(relevant))
    for i in range(1, ideal_hits + 1):
        idcg += (2.0**1.0 - 1.0) / math.log2(i + 1.0)

    if idcg <= 0.0:
        return 0.0
    return dcg / idcg


def context_precision(retrieved_chunks: Sequence[str], relevant_chunks: Set[str]) -> float:
    """Computes Context Precision: cumulative precision weighted by relevance position."""
    if not relevant_chunks or not retrieved_chunks:
        return 0.0
    return average_precision(retrieved_chunks, relevant_chunks)


def context_recall(retrieved_text: str, expected_passages: Sequence[str]) -> float:
    """Computes Context Recall: fraction of expected passages grounded in retrieved context."""
    if not expected_passages:
        return 1.0
    if not retrieved_text:
        return 0.0

    norm_context = retrieved_text.lower()
    matched = 0
    for p in expected_passages:
        clean_p = p.strip().lower()
        if not clean_p:
            continue
        # Direct substring match
        if clean_p in norm_context:
            matched += 1
        else:
            # Token overlap check (threshold 70% of passage tokens)
            p_tokens = set(clean_p.split())
            if p_tokens:
                ctx_tokens = set(norm_context.split())
                overlap = len(p_tokens.intersection(ctx_tokens))
                if overlap / len(p_tokens) >= 0.70:
                    matched += 1

    return matched / max(1, len(expected_passages))


def compute_all_retrieval_metrics(
    retrieved_chunk_ids: Sequence[str],
    expected_chunk_ids: Sequence[str],
    k_values: Tuple[int, ...] = (1, 3, 5, 10),
    retrieved_context_text: Optional[str] = None,
    expected_passages: Optional[Sequence[str]] = None,
) -> Dict[str, float]:
    """Computes all retrieval metrics across configured K thresholds."""
    relevant_set = set(expected_chunk_ids)
    metrics: Dict[str, float] = {}

    for k in k_values:
        metrics[f"precision@{k}"] = precision_at_k(retrieved_chunk_ids, relevant_set, k)
        metrics[f"recall@{k}"] = recall_at_k(retrieved_chunk_ids, relevant_set, k)
        metrics[f"hit_rate@{k}"] = hit_rate_at_k(retrieved_chunk_ids, relevant_set, k)
        metrics[f"ndcg@{k}"] = ndcg_at_k(retrieved_chunk_ids, relevant_set, k)

    metrics["mrr"] = reciprocal_rank(retrieved_chunk_ids, relevant_set)
    metrics["map"] = average_precision(retrieved_chunk_ids, relevant_set)
    metrics["context_precision"] = context_precision(retrieved_chunk_ids, relevant_set)

    if expected_passages is not None and retrieved_context_text is not None:
        metrics["context_recall"] = context_recall(retrieved_context_text, expected_passages)

    return metrics

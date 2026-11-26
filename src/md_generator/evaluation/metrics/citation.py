from __future__ import annotations

"""Citation & Reference Verification Metrics (Pure Python / Deterministic).

Phase 2F/Prompt 08 Implementation:
- Citation Precision: fraction of citations cited in the generated answer that resolve
  to genuine, valid retrieved chunks.
- Citation Recall: fraction of expected citations that were actually cited in the answer.
- Citation Continuity: verifies that no citations cite nonexistent or pruned evidence.
"""

import re
from typing import Dict, List, Optional, Sequence, Set


CITATION_REGEX = re.compile(r"\[(\d+)\]")


def extract_citation_indices(text: str) -> List[int]:
    """Extracts numeric citation markers (e.g. [1], [2]) from text."""
    if not text:
        return []
    matches = CITATION_REGEX.findall(text)
    return [int(m) for m in matches]


def citation_precision(
    generated_answer: str,
    available_citations_count: int,
) -> float:
    """Calculates Citation Precision = |valid cited indices| / |total cited indices|.
    
    A citation [N] is valid if 1 <= N <= available_citations_count.
    """
    cited = extract_citation_indices(generated_answer)
    if not cited:
        # If no citations were made, return 1.0 if no citations were available, else 0.0
        return 1.0 if available_citations_count == 0 else 0.0

    valid = sum(1 for idx in cited if 1 <= idx <= available_citations_count)
    return round(valid / len(cited), 4)


def citation_recall(
    generated_answer: str,
    expected_citations: Sequence[str],
) -> float:
    """Calculates Citation Recall = |expected citations cited| / |expected citations|."""
    if not expected_citations:
        return 1.0
    if not generated_answer:
        return 0.0

    cited_indices = set(extract_citation_indices(generated_answer))
    if not cited_indices:
        return 0.0

    matched = 0
    for exp in expected_citations:
        clean_exp = exp.strip().replace("[", "").replace("]", "")
        if clean_exp.isdigit() and int(clean_exp) in cited_indices:
            matched += 1
        elif exp in generated_answer:
            matched += 1

    return round(matched / len(expected_citations), 4)


def compute_all_citation_metrics(
    generated_answer: str,
    available_citations_count: int,
    expected_citations: Optional[Sequence[str]] = None,
) -> Dict[str, float]:
    """Aggregates citation precision and recall metrics."""
    metrics: Dict[str, float] = {
        "citation_precision": citation_precision(generated_answer, available_citations_count),
    }

    if expected_citations is not None:
        metrics["citation_recall"] = citation_recall(generated_answer, expected_citations)

    return metrics

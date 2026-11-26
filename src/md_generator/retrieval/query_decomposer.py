from __future__ import annotations

"""Deterministic Rule-Based Query Decomposer for MDEngine.

Splits compound, multi-condition, and comparative user questions into targeted subqueries
for multi-angle retrieval without requiring external AI/LLM models.
"""

import re
from typing import List, Protocol, Optional


COMPOUND_SPLITTERS = re.compile(
    r"\b(?:and\s+also|and\s+what\s+are|and\s+what\s+is|and\s+how\s+to|as\s+well\s+as|along\s+with|\band\b|\balso\b|;|vs\.?|versus)\b|\?",
    re.IGNORECASE,
)

QUESTION_PREFIX_PATTERN = re.compile(
    r"^(?:what\s+is|what\s+are|how\s+to|explain|describe|tell\s+me\s+about|details\s+of|guidelines\s+for)\s+",
    re.IGNORECASE,
)


class BaseQueryDecomposer(Protocol):
    """Protocol for query decomposition planners."""

    def decompose(self, query: str) -> List[str]:
        ...


class RuleBasedQueryDecomposer:
    """Pure-script deterministic query decomposer for compound questions."""

    def __init__(self, min_subquery_length: int = 3, max_subqueries: int = 4) -> None:
        self.min_subquery_length = min_subquery_length
        self.max_subqueries = max_subqueries

    def decompose(self, query: str) -> List[str]:
        """Break down a compound query into targeted subqueries."""
        if not query or not isinstance(query, str):
            return []

        clean_q = query.strip()
        # Always include the original query as the primary search intent
        subqueries: List[str] = [clean_q]

        # Extract core domain subject from the beginning of the query
        subject_match = QUESTION_PREFIX_PATTERN.sub("", clean_q)
        subject_words = subject_match.split()
        lead_subject = " ".join(subject_words[:3]) if len(subject_words) >= 3 else subject_match

        # Split on conjunctions and sentence breaks
        parts = COMPOUND_SPLITTERS.split(clean_q)
        clean_parts = [p.strip() for p in parts if p and len(p.strip().split()) >= self.min_subquery_length]

        if len(clean_parts) > 1:
            for part in clean_parts:
                normalized_part = QUESTION_PREFIX_PATTERN.sub("", part).strip()
                if normalized_part and normalized_part.lower() != clean_q.lower():
                    # If subquery lacks the lead subject, prepend it for context
                    if lead_subject.lower() not in normalized_part.lower():
                        enriched_part = f"{lead_subject} {normalized_part}".strip()
                        subqueries.append(enriched_part)
                    else:
                        subqueries.append(normalized_part)

        # Deduplicate while preserving order
        seen = set()
        deduped: List[str] = []
        for q in subqueries:
            q_norm = q.lower().strip()
            if q_norm not in seen:
                seen.add(q_norm)
                deduped.append(q)

        return deduped[: self.max_subqueries]

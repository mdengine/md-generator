from __future__ import annotations

"""Configurable Reranker Architecture: Base Protocol, Cross-Encoder, and Rule-Based Fallback.

Phase 1B/2A Implementation:
- Standardized BaseReranker interface for scoring candidates against user queries.
- RuleBasedReranker: 100% offline, zero-AI deterministic reranking (phrase proximity, title matching, term density).
- CrossEncoderReranker: Optional local neural cross-encoder (e.g. cross-encoder/ms-marco-MiniLM-L-6-v2) with strict offline support.
"""

import math
import re
from typing import Any, Dict, List, Optional, Protocol


class BaseReranker(Protocol):
    """Protocol for candidate rerankers."""

    def rerank(self, query: str, candidates: List[Any], top_k: int = 10) -> List[Any]:
        """Score and rerank candidate retrieval results."""
        ...


class RuleBasedReranker:
    """Deterministic, pure-script reranker boosting phrase matches, heading hits, and proximity."""

    def __init__(
        self,
        phrase_weight: float = 0.4,
        heading_weight: float = 0.3,
        proximity_weight: float = 0.3,
    ) -> None:
        self.phrase_weight = phrase_weight
        self.heading_weight = heading_weight
        self.proximity_weight = proximity_weight

    def rerank(self, query: str, candidates: List[Any], top_k: int = 10) -> List[Any]:
        """Rerank candidates based on lexical and structural features."""
        if not candidates or not query:
            return candidates[:top_k]

        q_lower = query.lower().strip()
        q_terms = [t for t in re.findall(r"\w+", q_lower) if len(t) >= 2]

        scored_candidates: List[Tuple[float, Any]] = []

        for cand in candidates:
            content = getattr(cand, "content", "") or getattr(cand, "sanitized_content", "") or ""
            content_lower = content.lower()
            base_score = float(getattr(cand, "score", 0.0) or getattr(cand, "hybrid_score", 0.0) or 0.0)

            # Feature 1: Exact Query or Phrase Match
            phrase_score = 1.0 if q_lower in content_lower else 0.0
            if not phrase_score and len(q_terms) >= 2:
                # Sub-phrase match (e.g. pairs of words together)
                for i in range(len(q_terms) - 1):
                    pair = f"{q_terms[i]} {q_terms[i+1]}"
                    if pair in content_lower:
                        phrase_score = max(phrase_score, 0.6)
                        break

            # Feature 2: Heading Match (# Section ...)
            heading_score = 0.0
            for line in content.splitlines()[:5]:
                if line.startswith("#") and any(t in line.lower() for t in q_terms):
                    heading_score = 1.0
                    break

            # Feature 3: Term Density / Proximity
            matched_terms = [t for t in q_terms if t in content_lower]
            density_score = len(matched_terms) / max(len(q_terms), 1)

            # Combined rerank boost
            boost = (
                self.phrase_weight * phrase_score
                + self.heading_weight * heading_score
                + self.proximity_weight * density_score
            )
            final_score = (0.5 * base_score) + (0.5 * boost)
            final_score = max(0.0, min(1.0, final_score))

            # Store updated score if possible
            if hasattr(cand, "hybrid_score"):
                setattr(cand, "hybrid_score", final_score)
            elif hasattr(cand, "score"):
                setattr(cand, "score", final_score)

            cid = getattr(cand, "chunk_id", "")
            scored_candidates.append((final_score, cid, cand))

        # Sort deterministically: (-final_score, cid)
        scored_candidates.sort(key=lambda x: (-x[0], x[1]))
        return [item[2] for item in scored_candidates[:top_k]]


class CrossEncoderReranker:
    """Optional neural cross-encoder reranker with strict offline loading support."""

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str = "cpu",
        offline_mode: bool = False,
        fallback_reranker: Optional[BaseReranker] = None,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.offline_mode = offline_mode
        self.fallback = fallback_reranker or RuleBasedReranker()
        self._model = None
        self._load_model()

    def _load_model(self) -> None:
        try:
            from sentence_transformers import CrossEncoder  # type: ignore
            model_kwargs = {}
            if self.offline_mode:
                model_kwargs["local_files_only"] = True
            self._model = CrossEncoder(self.model_name, device=self.device, **model_kwargs)
        except Exception:
            # Model or package not available; will use fallback
            self._model = None

    @property
    def is_available(self) -> bool:
        return self._model is not None

    def rerank(self, query: str, candidates: List[Any], top_k: int = 10) -> List[Any]:
        """Rerank candidates using cross-encoder scores or fallback."""
        if not candidates or not query:
            return candidates[:top_k]

        if self._model is None:
            return self.fallback.rerank(query, candidates, top_k)

        pairs = []
        for cand in candidates:
            content = getattr(cand, "content", "") or getattr(cand, "sanitized_content", "") or ""
            pairs.append([query, content])

        try:
            raw_scores = self._model.predict(pairs)
            scored: List[Tuple[float, str, Any]] = []

            for idx, cand in enumerate(candidates):
                raw_s = float(raw_scores[idx])
                # Sigmoid normalization for cross-encoder logits
                norm_score = 1.0 / (1.0 + math.exp(-raw_s))
                norm_score = max(0.0, min(1.0, norm_score))

                if hasattr(cand, "hybrid_score"):
                    setattr(cand, "hybrid_score", norm_score)
                elif hasattr(cand, "score"):
                    setattr(cand, "score", norm_score)

                cid = getattr(cand, "chunk_id", "")
                scored.append((norm_score, cid, cand))

            scored.sort(key=lambda x: (-x[0], x[1]))
            return [item[2] for item in scored[:top_k]]
        except Exception:
            # On unexpected runtime error, gracefully use fallback
            return self.fallback.rerank(query, candidates, top_k)

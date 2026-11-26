from __future__ import annotations

"""Pure-Script Extractive Chat Provider (Default Mode).

Phase 2D/Prompt 06 Implementation:
- 100% offline, zero-AI, pure Python execution.
- Extractive answer synthesis directly from authentic retrieved document passages.
- Links exact source citations (#page=N, #slide=N, #section=S).
- Deterministic insufficient-evidence handling: never generates unsupported factual claims.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from md_generator.adapters.langchain.context import estimate_token_count
from md_generator.chat.models import ChatMessage
from md_generator.chat.providers.base import BaseChatProvider
from md_generator.context.manager import AssembledContext


INSUFFICIENT_EVIDENCE_RESPONSE = (
    "Insufficient evidence in the available documents to answer the question."
)


def _tokenize_words(text: str) -> Set[str]:
    """Extracts non-stop lowercase alphanumeric words."""
    words = re.findall(r"\b[A-Za-z0-9_-]{2,}\b", text.lower())
    stop_words = {
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
        "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
        "below", "between", "both", "but", "by", "can", "cannot", "could", "couldn't",
        "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
        "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
        "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
        "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
        "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
        "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
        "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or",
        "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same",
        "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
        "some", "such", "than", "that", "that's", "the", "their", "theirs", "them",
        "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll",
        "they're", "they've", "this", "those", "through", "to", "too", "under", "until",
        "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've",
        "were", "weren't", "what", "what's", "when", "when's", "where", "where's",
        "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't",
        "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your",
        "yours", "yourself", "yourselves", "tell", "please", "give", "show", "find"
    }
    return {w for w in words if w not in stop_words}


def _split_sentences(text: str) -> List[str]:
    """Splits passage into clean sentences, preserving common abbreviations with dots."""
    if not text:
        return []
    # Protect common abbreviations
    protected = re.sub(
        r"\b(Dr|Mr|Mrs|Ms|Prof|Sr|Jr|Inc|Corp|Ltd|Co|vs|e\.g|i\.e)\.",
        lambda m: m.group(0).replace(".", "@@DOT@@"),
        text.strip(),
        flags=re.IGNORECASE,
    )
    parts = re.split(r"(?<=[.!?])\s+", protected)
    sentences = []
    for s in parts:
        clean = s.replace("@@DOT@@", ".").strip()
        # Strip leading markdown headers (e.g. ## Page 1\n)
        clean = re.sub(r"^#{1,6}\s+[^\n]*\r?\n+", "", clean).strip()
        if len(clean) > 10 and not clean.startswith("#"):
            sentences.append(clean)
    return sentences


class ExtractiveChatProvider(BaseChatProvider):
    """Generates strictly grounded answers extracted directly from retrieved passages."""

    def __init__(
        self,
        min_relevance_overlap: float = 0.1,
        max_extracted_sentences: int = 4,
    ) -> None:
        self.min_relevance_overlap = min_relevance_overlap
        self.max_extracted_sentences = max_extracted_sentences

    def generate_response(
        self,
        query: str,
        context: AssembledContext,
        history: List[ChatMessage],
        system_instructions: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Dict[str, int]]:
        """Synthesizes extractive answer from retrieved evidence."""
        prompt_tokens = context.token_count
        query_words = _tokenize_words(query)

        # 1. Check for empty context or missing chunks
        if not context.included_chunks or not context.context_text:
            return INSUFFICIENT_EVIDENCE_RESPONSE, {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": estimate_token_count(INSUFFICIENT_EVIDENCE_RESPONSE),
                "total_tokens": prompt_tokens + estimate_token_count(INSUFFICIENT_EVIDENCE_RESPONSE),
            }

        # 2. Extract and score sentences from each included chunk
        scored_sentences: List[Tuple[float, str, int]] = []  # (score, sentence_text, cit_index)

        for idx, chunk in enumerate(context.included_chunks, start=1):
            content = (
                getattr(chunk, "sanitized_content", "")
                or getattr(chunk, "page_content", "")
                or getattr(chunk, "content", "")
                or (chunk.get("content") if isinstance(chunk, dict) else "")
                or ""
            )
            # Remove markdown table borders for clean sentence extraction
            cleaned_content = re.sub(r"\|", " ", content)
            sentences = _split_sentences(cleaned_content)

            for s in sentences:
                s_words = _tokenize_words(s)
                if not s_words:
                    continue

                overlap = len(query_words.intersection(s_words))
                if overlap > 0:
                    score = overlap / max(1, len(query_words))
                    if score >= self.min_relevance_overlap:
                        scored_sentences.append((score, s, idx))

        # 3. Insufficient evidence fallback if no sentences matched
        if not scored_sentences:
            return INSUFFICIENT_EVIDENCE_RESPONSE, {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": estimate_token_count(INSUFFICIENT_EVIDENCE_RESPONSE),
                "total_tokens": prompt_tokens + estimate_token_count(INSUFFICIENT_EVIDENCE_RESPONSE),
            }

        # Sort sentences by relevance score descending
        scored_sentences.sort(key=lambda item: -item[0])
        top_sentences = scored_sentences[:self.max_extracted_sentences]

        # 4. Assemble synthesized answer
        answer_parts: List[str] = ["Based on the retrieved documents:\n"]
        used_citation_indices: Set[int] = set()

        for score, sent, cit_idx in top_sentences:
            used_citation_indices.add(cit_idx)
            answer_parts.append(f"- {sent} [{cit_idx}]")

        answer_text = "\n".join(answer_parts)

        # 5. Append references if citations available
        relevant_citations = [
            context.citations[i - 1]
            for i in sorted(list(used_citation_indices))
            if 0 <= i - 1 < len(context.citations)
        ]

        if relevant_citations:
            ref_lines: List[str] = ["\n### References"]
            for cit_idx in sorted(list(used_citation_indices)):
                if 0 <= cit_idx - 1 < len(context.citations):
                    cit = context.citations[cit_idx - 1]
                    link = cit.format_link()
                    doc_label = f"Document: `{cit.document_id[:16]}...`" if len(cit.document_id) > 20 else f"Document: `{cit.document_id}`"
                    loc_parts = []
                    if cit.page is not None:
                        loc_parts.append(f"Page {cit.page}")
                    if cit.slide is not None:
                        loc_parts.append(f"Slide {cit.slide}")
                    if cit.section is not None:
                        loc_parts.append(f"Section {cit.section}")
                    loc_str = f" ({', '.join(loc_parts)})" if loc_parts else ""

                    if link:
                        ref_lines.append(f"[{cit_idx}] {doc_label}{loc_str} — [{link}]({link})")
                    else:
                        ref_lines.append(f"[{cit_idx}] {doc_label}{loc_str}")

            answer_text = f"{answer_text}\n" + "\n".join(ref_lines)

        completion_tokens = estimate_token_count(answer_text)
        return answer_text, {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }

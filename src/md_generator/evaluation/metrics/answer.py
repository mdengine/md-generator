from __future__ import annotations

"""Answer Quality & Faithfulness Metrics (Pure Python / Deterministic).

Phase 2F/Prompt 08 Implementation:
- Faithfulness / Groundedness: measures whether answer statements are factually supported
  by retrieved context (sentence-by-sentence support checking, entity & numeric verification).
- Answer Relevance: measures keyword, entity, and question intent overlap between query and answer.
- Evidence Coverage: fraction of key entities and facts from expected ground truth covered in the answer.
- Context Utilization: fraction of retrieved passages actually cited or referenced in the response.
- Semantic Overlap Similarity: normalized character/token Jaccard similarity against ground truth.

Important: Deterministic heuristics represent textual support signals, not external factual truth.
"""

import re
from typing import Dict, List, Optional, Set, Tuple


STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "hers", "herself", "him", "himself", "his", "how", "i", "i'm", "if", "in",
    "into", "is", "isn't", "it", "it's", "its", "itself", "me", "more", "most",
    "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or",
    "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same",
    "she", "should", "so", "some", "such", "than", "that", "the", "their",
    "theirs", "them", "themselves", "then", "there", "these", "they", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasn't", "we", "were", "what", "when", "where", "which", "while", "who",
    "whom", "why", "with", "would", "you", "your", "yours", "yourself"
}


def _tokenize(text: str) -> Set[str]:
    """Tokenizes alphanumeric words excluding stopwords, with basic suffix normalization."""
    words = re.findall(r"\b[A-Za-z0-9_-]{2,}\b", text.lower())
    result: Set[str] = set()
    for w in words:
        if w in STOP_WORDS:
            continue
        # Basic plural suffix stripping
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        result.add(w)
    return result


def _extract_numbers_and_entities(text: str) -> Set[str]:
    """Extracts numeric values, acronyms, and capitalized entities."""
    numbers = set(re.findall(r"\b\d+(?:\.\d+)?(?:%|ms|gb|mb|tb|dbm|k)?\b", text.lower()))
    caps = set(re.findall(r"\b[A-Z][a-zA-Z0-9_-]{2,}\b", text))
    return numbers.union({c.lower() for c in caps})


def _split_sentences(text: str) -> List[str]:
    """Splits answer into sentences, protecting titles and abbreviations."""
    if not text:
        return []
    protected = re.sub(
        r"\b(Dr|Mr|Mrs|Ms|Prof|Inc|Corp|Ltd|Co|e\.g|i\.e|vs)\.",
        lambda m: m.group(0).replace(".", "@@DOT@@"),
        text.strip(),
        flags=re.IGNORECASE,
    )
    parts = re.split(r"(?<=[.!?])\s+", protected)
    sentences = []
    for p in parts:
        clean = p.replace("@@DOT@@", ".").strip()
        # Filter out markdown headers, bullets or short fragments
        if len(clean) > 8 and not clean.startswith("#") and not clean.startswith("### References"):
            sentences.append(clean)
    return sentences


def faithfulness_score(generated_answer: str, retrieved_context: str) -> float:
    """Calculates Faithfulness / Groundedness score (0.0 to 1.0).
    
    Verifies that claims in each sentence of the generated answer are grounded
    in the retrieved context. Sentences containing hallucinated numbers or unknown
    entities without context support are penalized.
    """
    if not generated_answer or not generated_answer.strip():
        return 0.0
    if not retrieved_context or not retrieved_context.strip():
        # Any factual claim without context is ungrounded (0.0)
        return 0.0

    # Strip citation reference bibliography footer before claim verification
    clean_answer = generated_answer
    if "### References" in clean_answer:
        clean_answer = clean_answer.split("### References")[0]

    sentences = _split_sentences(clean_answer)
    if not sentences:
        return 1.0

    context_tokens = _tokenize(retrieved_context)
    context_entities = _extract_numbers_and_entities(retrieved_context)

    supported_count = 0.0

    for sent in sentences:
        sent_tokens = _tokenize(sent)
        if not sent_tokens:
            supported_count += 1.0
            continue

        # 1. Token overlap with context
        overlap = len(sent_tokens.intersection(context_tokens))
        token_support = overlap / len(sent_tokens)

        # 2. Number and entity verification
        sent_entities = _extract_numbers_and_entities(sent)
        if sent_entities:
            entity_overlap = len(sent_entities.intersection(context_entities))
            entity_support = entity_overlap / len(sent_entities)
        else:
            entity_support = 1.0

        # Both token support and entity support must be adequate
        if token_support >= 0.50 and entity_support >= 0.70:
            supported_count += 1.0
        elif token_support >= 0.35 and entity_support == 1.0:
            supported_count += 0.8
        else:
            supported_count += 0.0

    return round(supported_count / len(sentences), 4)


def answer_relevance(query: str, generated_answer: str) -> float:
    """Calculates Answer Relevance (0.0 to 1.0) based on query intent and entity coverage."""
    if not query or not generated_answer:
        return 0.0

    q_tokens = _tokenize(query)
    if not q_tokens:
        return 1.0

    ans_tokens = _tokenize(generated_answer)
    overlap = len(q_tokens.intersection(ans_tokens))
    score = overlap / len(q_tokens)

    # Check for direct insufficient evidence response
    if "insufficient evidence" in generated_answer.lower():
        # Valid rejection of ungrounded questions
        return 1.0 if score > 0 else 0.5

    return min(1.0, round(score, 4))


def evidence_coverage(expected_answer: str, generated_answer: str) -> float:
    """Calculates Evidence Coverage: fraction of key entities and facts in ground truth covered."""
    if not expected_answer:
        return 1.0
    if not generated_answer:
        return 0.0

    expected_facts = _extract_numbers_and_entities(expected_answer)
    if not expected_facts:
        expected_facts = _tokenize(expected_answer)
    if not expected_facts:
        return 1.0

    ans_facts = _extract_numbers_and_entities(generated_answer).union(_tokenize(generated_answer))
    covered = len(expected_facts.intersection(ans_facts))
    return round(covered / len(expected_facts), 4)


def token_overlap_similarity(text1: str, text2: str) -> float:
    """Calculates Jaccard token overlap similarity between two text snippets."""
    if not text1 and not text2:
        return 1.0
    if not text1 or not text2:
        return 0.0

    t1 = _tokenize(text1)
    t2 = _tokenize(text2)
    if not t1 and not t2:
        return 1.0
    union = t1.union(t2)
    if not union:
        return 0.0
    return round(len(t1.intersection(t2)) / len(union), 4)


def context_utilization(generated_answer: str, retrieved_context: str) -> float:
    """Calculates Context Utilization: ratio of retrieved context paragraphs reflected in the answer."""
    if not generated_answer or not retrieved_context:
        return 0.0

    paragraphs = [p.strip() for p in retrieved_context.split("\n\n") if len(p.strip()) > 20]
    if not paragraphs:
        return 0.0

    ans_tokens = _tokenize(generated_answer)
    utilized = 0
    for p in paragraphs:
        p_tokens = _tokenize(p)
        if p_tokens and len(p_tokens.intersection(ans_tokens)) >= 2:
            utilized += 1

    return round(utilized / len(paragraphs), 4)


def compute_all_answer_metrics(
    query: str,
    generated_answer: str,
    retrieved_context: str,
    ground_truth_answer: Optional[str] = None,
) -> Dict[str, float]:
    """Aggregates all deterministic answer quality metrics."""
    metrics: Dict[str, float] = {
        "faithfulness": faithfulness_score(generated_answer, retrieved_context),
        "answer_relevance": answer_relevance(query, generated_answer),
        "context_utilization": context_utilization(generated_answer, retrieved_context),
    }

    if ground_truth_answer:
        metrics["evidence_coverage"] = evidence_coverage(ground_truth_answer, generated_answer)
        metrics["semantic_similarity"] = token_overlap_similarity(ground_truth_answer, generated_answer)

    return metrics

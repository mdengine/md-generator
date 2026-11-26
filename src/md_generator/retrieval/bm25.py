from __future__ import annotations

"""Pure-script BM25Okapi Lexical Indexer & Ranker for MDEngine Phase 1B/2A.

Standard library only implementation of Okapi BM25 with document length normalization (k1=1.5, b=0.75),
token frequency caching, multi-tenant candidate scoping, and JSON index persistence.
"""

from collections import Counter
import json
import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple


STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does",
    "doesn't", "doing", "don't", "down", "during", "each", "few", "for", "from", "further", "had",
    "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd",
    "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself",
    "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off",
    "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own",
    "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through",
    "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're",
    "we've", "were", "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you",
    "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves",
}

TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]{2,}")


def tokenize(text: str, filter_stopwords: bool = True) -> List[str]:
    """Tokenize text into lowercase alphanumeric terms with optional stopword filtering."""
    if not text or not isinstance(text, str):
        return []
    tokens = TOKEN_PATTERN.findall(text.lower())
    if filter_stopwords:
        return [t for t in tokens if t not in STOPWORDS]
    return tokens


class BM25Index:
    """Okapi BM25 index supporting incremental document upsert, multi-tenancy, and persistence."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = float(k1)
        self.b = float(b)
        # Store document records: doc_id -> metadata
        self._doc_map: Dict[str, Dict[str, Any]] = {}
        # Document frequencies: term -> count of documents containing term
        self._df: Counter[str] = Counter()
        # Document term frequencies: doc_id -> Counter(term -> count)
        self._tf: Dict[str, Counter[str]] = {}
        # Document length (token count): doc_id -> int
        self._doc_len: Dict[str, int] = {}
        # Tenant indexing: tenant_id -> set of doc_ids
        self._tenant_docs: Dict[str, Set[str]] = {}

    @property
    def total_documents(self) -> int:
        return len(self._doc_map)

    @property
    def average_document_length(self) -> float:
        if not self._doc_len:
            return 0.0
        return sum(self._doc_len.values()) / max(len(self._doc_len), 1)

    def add_document(
        self,
        doc_id: str,
        text: str,
        tenant_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add or update a document in the BM25 index."""
        if not doc_id:
            raise ValueError("doc_id must be non-empty.")
        if not tenant_id:
            raise ValueError("tenant_id must be non-empty.")

        # If document already exists, remove it first to avoid duplicate counts
        if doc_id in self._doc_map:
            self.remove_document(doc_id)

        tokens = tokenize(text)
        tf = Counter(tokens)
        doc_len = len(tokens)

        self._doc_map[doc_id] = {
            "doc_id": doc_id,
            "text": text,
            "tenant_id": tenant_id,
            "metadata": metadata or {},
        }
        self._tf[doc_id] = tf
        self._doc_len[doc_id] = doc_len

        for term in tf.keys():
            self._df[term] += 1

        if tenant_id not in self._tenant_docs:
            self._tenant_docs[tenant_id] = set()
        self._tenant_docs[tenant_id].add(doc_id)

    def add_documents(self, documents: List[Dict[str, Any]], tenant_id: str) -> int:
        """Batch add documents to the index."""
        count = 0
        for doc in documents:
            did = doc.get("chunk_id") or doc.get("doc_id") or doc.get("id")
            text = doc.get("content") or doc.get("text") or doc.get("sanitized_content") or ""
            meta = doc.get("metadata") or {}
            if did:
                self.add_document(doc_id=did, text=text, tenant_id=tenant_id, metadata=meta)
                count += 1
        return count

    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from the BM25 index."""
        if doc_id not in self._doc_map:
            return False

        tf = self._tf.pop(doc_id, Counter())
        self._doc_len.pop(doc_id, None)
        doc_info = self._doc_map.pop(doc_id)

        tenant_id = doc_info.get("tenant_id")
        if tenant_id and tenant_id in self._tenant_docs:
            self._tenant_docs[tenant_id].discard(doc_id)

        for term in tf.keys():
            self._df[term] -= 1
            if self._df[term] <= 0:
                del self._df[term]

        return True

    def search(
        self,
        query: str,
        top_k: int = 50,
        tenant_id: Optional[str] = None,
    ) -> List[Tuple[str, float]]:
        """Compute Okapi BM25 scores for query matching against indexed documents."""
        q_terms = tokenize(query)
        if not q_terms or not self._doc_map:
            return []

        # Filter candidate documents by tenant if specified
        if tenant_id:
            candidate_doc_ids = self._tenant_docs.get(tenant_id, set())
        else:
            candidate_doc_ids = set(self._doc_map.keys())

        if not candidate_doc_ids:
            return []

        n_total = len(candidate_doc_ids)
        avgdl = sum(self._doc_len[did] for did in candidate_doc_ids) / max(n_total, 1)

        scores: List[Tuple[str, float]] = []

        for did in candidate_doc_ids:
            tf_doc = self._tf[did]
            dl = self._doc_len[did]
            score = 0.0

            for term in q_terms:
                if term not in tf_doc:
                    continue
                # Document frequency of term within scope
                n_qi = self._df.get(term, 0)
                # Standard Okapi IDF
                idf = math.log(1.0 + (n_total - n_qi + 0.5) / (n_qi + 0.5))
                f = tf_doc[term]
                denom = f + self.k1 * (1.0 - self.b + self.b * (dl / max(avgdl, 1.0)))
                score += idf * (f * (self.k1 + 1.0)) / max(denom, 1e-9)

            if score > 0.0:
                scores.append((did, score))

        # Sort deterministically: (-score, doc_id)
        scores.sort(key=lambda item: (-item[1], item[0]))
        return scores[:top_k]

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve document metadata by doc_id."""
        return self._doc_map.get(doc_id)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize index state to canonical dictionary."""
        return {
            "k1": self.k1,
            "b": self.b,
            "doc_map": self._doc_map,
            "doc_len": self._doc_len,
            "df": dict(self._df),
            "tenant_docs": {k: list(v) for k, v in self._tenant_docs.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BM25Index:
        """Deserialize index state from dictionary."""
        idx = cls(k1=data.get("k1", 1.5), b=data.get("b", 0.75))
        idx._doc_map = data.get("doc_map", {})
        idx._doc_len = data.get("doc_len", {})
        idx._df = Counter(data.get("df", {}))
        for did, dinfo in idx._doc_map.items():
            text = dinfo.get("text", "")
            idx._tf[did] = Counter(tokenize(text))
        raw_tenants = data.get("tenant_docs", {})
        idx._tenant_docs = {k: set(v) for k, v in raw_tenants.items()}
        return idx

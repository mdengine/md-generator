from __future__ import annotations

"""Evidence Validator: Grounding, Hallucination Detection & Evidence Consistency.

Phase 1C/Prompt 04 Implementation:
- Validates that citations in generated text or candidate responses correspond to authentic retrieved chunks.
- Flags hallucinated citations, missing evidence backing, and conflicting claims across evidence chunks.
- Computes sentence-level grounding coverage ratios and verifies claims against source content.
"""

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from md_generator.context.citation import Citation, CitationManager


@dataclass
class EvidenceConflict:
    """Represents a factual or semantic contradiction between evidence pieces or between claim and source."""
    entity: str
    claim_a: str
    claim_b: str
    source_a: str
    source_b: str
    conflict_type: str = "numerical"  # "numerical", "negation", "status", "temporal"


@dataclass
class EvidenceValidationResult:
    """Detailed summary of evidence validation and grounding checks."""
    is_valid: bool
    coverage_ratio: float
    supported_citations: List[Citation] = field(default_factory=list)
    hallucinated_citations: List[str] = field(default_factory=list)
    missing_citations_count: int = 0
    unsupported_sentences: List[str] = field(default_factory=list)
    conflicts: List[EvidenceConflict] = field(default_factory=list)
    validation_notes: List[str] = field(default_factory=list)


def _split_into_sentences(text: str) -> List[str]:
    """Deterministic standard-library sentence tokenizer."""
    if not text:
        return []
    # Split on sentence terminals followed by whitespace
    raw = re.split(r"(?<=[.!?])\s+", text.strip())
    # Filter out empty or whitespace-only lines
    return [s.strip() for s in raw if s.strip() and not s.strip().startswith("#")]


def _extract_numbers_and_entities(text: str) -> Set[str]:
    """Extracts numeric values, percentages, currency, and uppercase terms for grounding check."""
    tokens: Set[str] = set()
    # Numbers, percentages, currency
    for m in re.finditer(r"\b(?:\$|€|£)?\d+(?:[.,]\d+)?%?\b", text):
        tokens.add(m.group(0).lower())
    # Technical acronyms / capitalized proper nouns (2+ letters)
    for m in re.finditer(r"\b[A-Z][A-Za-z0-9_-]{2,}\b", text):
        tokens.add(m.group(0).lower())
    return tokens


class EvidenceValidator:
    """Validates citations, detects hallucinations, and flags conflicts in retrieved or generated context."""

    def __init__(
        self,
        min_coverage_ratio: float = 0.5,
        strict_grounding: bool = False,
        citation_manager: Optional[CitationManager] = None,
    ) -> None:
        self.min_coverage_ratio = float(min_coverage_ratio)
        self.strict_grounding = strict_grounding
        self.citation_manager = citation_manager or CitationManager()

    def validate(
        self,
        response_text: str,
        evidence_items: List[Any],
    ) -> EvidenceValidationResult:
        """Performs full evidence grounding and citation resolution validation."""
        if not response_text or not response_text.strip():
            return EvidenceValidationResult(
                is_valid=True,
                coverage_ratio=1.0,
                validation_notes=["Empty response text requires no validation."],
            )

        # Step 1: Map available evidence items to known identifiers and text
        available_citations: List[Citation] = []
        known_chunk_ids: Set[str] = set()
        known_doc_ids: Set[str] = set()
        chunk_content_map: Dict[str, str] = {}
        all_evidence_text: List[str] = []

        for idx, item in enumerate(evidence_items, start=1):
            cit = self.citation_manager.from_item(item, index=idx)
            available_citations.append(cit)
            if cit.chunk_id:
                known_chunk_ids.add(cit.chunk_id.lower())
                chunk_content_map[cit.chunk_id.lower()] = cit.preview_text.lower()
            if cit.document_id:
                known_doc_ids.add(cit.document_id.lower())

            # Collect content
            content = (
                getattr(item, "page_content", "")
                or getattr(item, "sanitized_content", "")
                or getattr(item, "content", "")
                or cit.preview_text
            )
            all_evidence_text.append(content.lower())
            if cit.chunk_id:
                chunk_content_map[cit.chunk_id.lower()] = content.lower()

        combined_evidence = " ".join(all_evidence_text)

        # Step 2: Extract citations from response text
        extracted_refs = self.citation_manager.extract_citations_from_text(response_text)

        supported_citations: List[Citation] = []
        hallucinated_citations: List[str] = []
        resolved_indices: Set[int] = set()

        for ref in extracted_refs:
            ref_type = ref.get("type")
            if ref_type in ("header", "tag"):
                c_id = (ref.get("chunk_id") or "").lower()
                d_id = (ref.get("document_id") or "").lower()

                matched = False
                for cit in available_citations:
                    if c_id and cit.chunk_id and cit.chunk_id.lower() == c_id:
                        supported_citations.append(cit)
                        matched = True
                        break
                    elif not c_id and d_id and cit.document_id.lower() == d_id:
                        supported_citations.append(cit)
                        matched = True
                        break

                if not matched:
                    raw_tag = ref.get("raw", f"Chunk:{c_id}")
                    hallucinated_citations.append(raw_tag)

            elif ref_type == "numbered":
                idx = ref.get("index", 0)
                if 1 <= idx <= len(available_citations):
                    supported_citations.append(available_citations[idx - 1])
                    resolved_indices.add(idx)
                else:
                    hallucinated_citations.append(f"[{idx}]")

        # Step 3: Sentence-level grounding check
        sentences = _split_into_sentences(response_text)
        grounded_count = 0
        factual_sentence_count = 0
        unsupported_sentences: List[str] = []
        missing_citations = 0

        for sentence in sentences:
            sentence_lower = sentence.lower()
            key_tokens = _extract_numbers_and_entities(sentence)

            if not key_tokens:
                # Conversational / connective sentence without factual assertions
                grounded_count += 1
                continue

            factual_sentence_count += 1
            has_explicit_citation = any(
                ref.get("raw", "") in sentence for ref in extracted_refs
            )

            # Check if key tokens are grounded in the combined evidence
            grounded_tokens = [t for t in key_tokens if t in combined_evidence]
            is_grounded = len(grounded_tokens) >= max(1, len(key_tokens) // 2)

            if is_grounded:
                grounded_count += 1
                if not has_explicit_citation and len(key_tokens) >= 2:
                    missing_citations += 1
            else:
                unsupported_sentences.append(sentence)

        coverage_ratio = (
            grounded_count / max(1, len(sentences))
            if sentences
            else 1.0
        )

        # Step 4: Detect conflicting evidence across retrieved chunks
        conflicts: List[EvidenceConflict] = self.detect_conflicts(evidence_items)

        # Step 5: Determine validity
        notes: List[str] = []
        is_valid = True

        if hallucinated_citations:
            is_valid = False
            notes.append(f"Detected {len(hallucinated_citations)} hallucinated or ungrounded citation(s).")

        if conflicts:
            notes.append(f"Detected {len(conflicts)} potential evidence conflict(s) among source chunks.")
            if self.strict_grounding:
                is_valid = False

        if coverage_ratio < self.min_coverage_ratio:
            is_valid = False
            notes.append(
                f"Grounding coverage ratio {coverage_ratio:.2f} is below required threshold {self.min_coverage_ratio:.2f}."
            )

        if is_valid:
            notes.append("All citations resolved successfully against evidence.")

        return EvidenceValidationResult(
            is_valid=is_valid,
            coverage_ratio=round(coverage_ratio, 4),
            supported_citations=supported_citations,
            hallucinated_citations=hallucinated_citations,
            missing_citations_count=missing_citations,
            unsupported_sentences=unsupported_sentences,
            conflicts=conflicts,
            validation_notes=notes,
        )

    def detect_conflicts(self, items: List[Any]) -> List[EvidenceConflict]:
        """Detects contradictions (numerical, negation, status) across retrieved evidence items."""
        if len(items) < 2:
            return []

        conflicts: List[EvidenceConflict] = []
        extracted_data: List[Dict[str, Any]] = []

        # Extract claims per item
        for item in items:
            if isinstance(item, dict):
                cid = item.get("chunk_id", "unknown_chunk")
                content = (
                    item.get("page_content")
                    or item.get("sanitized_content")
                    or item.get("content")
                    or ""
                )
            else:
                cid = getattr(item, "chunk_id", "unknown_chunk")
                content = (
                    getattr(item, "page_content", "")
                    or getattr(item, "sanitized_content", "")
                    or getattr(item, "content", "")
                )
            # Find status patterns: status: <active|inactive|pending|completed>
            for m in re.finditer(r"(?i)\bstatus[:\s=]+(active|inactive|pending|completed|deprecated|approved|rejected)\b", content):
                extracted_data.append({
                    "type": "status",
                    "entity": "status",
                    "value": m.group(1).lower(),
                    "claim": m.group(0),
                    "source": str(cid),
                })

            # Find numerical metrics: <metric> is/was/reached <number>
            for m in re.finditer(r"(?i)\b([a-zA-Z]{3,15})\s+(?:is|was|of|reached|at)\s+([\$€£]?\d+(?:\.\d+)?%?)\b", content):
                extracted_data.append({
                    "type": "numerical",
                    "entity": m.group(1).lower(),
                    "value": m.group(2).lower(),
                    "claim": m.group(0),
                    "source": str(cid),
                })

            # Find negation patterns: <subject> is (not )?<action/supported>
            for m in re.finditer(r"(?i)\b([a-zA-Z]{3,15})\s+is\s+(not\s+supported|supported|allowed|forbidden|enabled|disabled)\b", content):
                extracted_data.append({
                    "type": "negation",
                    "entity": m.group(1).lower(),
                    "value": m.group(2).lower(),
                    "claim": m.group(0),
                    "source": str(cid),
                })

        # Compare pairs across different sources
        for i in range(len(extracted_data)):
            for j in range(i + 1, len(extracted_data)):
                d1 = extracted_data[i]
                d2 = extracted_data[j]
                if d1["source"] == d2["source"]:
                    continue
                if d1["entity"] == d2["entity"] and d1["type"] == d2["type"]:
                    if d1["value"] != d2["value"]:
                        # Contradiction detected
                        conflicts.append(EvidenceConflict(
                            entity=d1["entity"],
                            claim_a=d1["claim"],
                            claim_b=d2["claim"],
                            source_a=d1["source"],
                            source_b=d2["source"],
                            conflict_type=d1["type"],
                        ))

        return conflicts

from __future__ import annotations

"""Pure-Script Rule-Based Entity & Relationship Extraction Engine.

Phase 2C/Prompt 05 Implementation:
- Extracts structural and domain entities (Organization, Person, Product, Location, Concept, Business Term).
- Generates canonical, collision-safe 64-character SHA-256 entity identities.
- Extracts co-occurrence and semantic relationships without requiring an external LLM.
- Fully offline, deterministic, and pure standard-library based.
"""

from abc import ABC, abstractmethod
import hashlib
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from md_generator.semantic.model.schema import Entity, Relationship, SourceLocation


def _compute_deterministic_hex_id(seed_str: str) -> str:
    """Computes a deterministic 64-character hex string SHA-256 identity."""
    return hashlib.sha256(seed_str.encode("utf-8")).hexdigest()


class BaseEntityExtractor(ABC):
    """Abstract interface for entity and relationship extraction."""

    @abstractmethod
    def extract_entities(
        self,
        text: str,
        source_location: Optional[SourceLocation] = None,
    ) -> List[Entity]:
        """Extracts domain entities from raw or markdown text."""
        pass

    @abstractmethod
    def extract_relationships(
        self,
        text: str,
        entities: List[Entity],
    ) -> List[Relationship]:
        """Extracts semantic relationships among extracted entities."""
        pass

    def extract(
        self,
        text: str,
        source_location: Optional[SourceLocation] = None,
    ) -> Tuple[List[Entity], List[Relationship]]:
        """Extracts both entities and their relationships from text."""
        entities = self.extract_entities(text, source_location=source_location)
        relationships = self.extract_relationships(text, entities)
        return entities, relationships


class RuleBasedEntityExtractor(BaseEntityExtractor):
    """Deterministic, rule-based entity and relationship extractor."""

    def __init__(
        self,
        enable_concepts: bool = True,
        min_acronym_length: int = 2,
        max_acronym_length: int = 6,
    ) -> None:
        self.enable_concepts = enable_concepts
        self.min_acronym_length = min_acronym_length
        self.max_acronym_length = max_acronym_length

        # Entity regex patterns
        self._org_pattern = re.compile(
            r"\b([A-Z][A-Za-z0-9&]+(?:\s+[A-Z][A-Za-z0-9&]+)*(?:\s+(?:Corp|Corporation|Inc|LLC|Ltd|Group|Company|Co|Agency|System|Department|Division|Labs|Technologies|Bank|Health|University)))\b"
        )
        self._person_pattern = re.compile(
            r"\b(?:Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.|President|CEO|CTO|Director)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"
        )
        self._product_pattern = re.compile(
            r"\b([A-Z][A-Za-z0-9_-]+(?:\s+(?:v\d+|version\s+\d+|\d+\.\d+|Pro|Enterprise|Studio|Engine|Platform|Suite|Service)))\b"
        )
        self._location_pattern = re.compile(
            r"\b(New York|San Francisco|London|Tokyo|Berlin|Paris|California|Germany|Japan|United States|UK|Canada|Australia|Singapore)\b"
        )
        self._acronym_pattern = re.compile(
            rf"\b[A-Z]{{{min_acronym_length},{max_acronym_length}}}\b"
        )
        self._camel_concept_pattern = re.compile(
            r"\b[A-Z][a-z]+[A-Z][a-zA-Z0-9]*\b"
        )

        # Stop words to filter false-positive acronyms/concepts
        self._stop_words = {
            "THE", "AND", "FOR", "WITH", "FROM", "THAT", "THIS", "HAVE", "BEEN",
            "PAGE", "DOC", "PDF", "ITEM", "NOTE", "TEST", "TRUE", "NONE",
        }

    def normalize_name(self, name: str) -> str:
        """Normalizes entity name by collapsing whitespace and trimming punctuation."""
        return re.sub(r"\s+", " ", name.strip().strip(".,;:\"'()[]{}"))

    def extract_entities(
        self,
        text: str,
        source_location: Optional[SourceLocation] = None,
    ) -> List[Entity]:
        """Extracts domain entities using high-precision regex rules."""
        if not text or not text.strip():
            return []

        discovered: Dict[str, Entity] = {}

        def _add_entity(ent_type: str, raw_name: str, confidence: float = 0.9) -> None:
            norm_name = self.normalize_name(raw_name)
            if not norm_name or len(norm_name) < 2 or norm_name.upper() in self._stop_words:
                return

            qualified = f"{ent_type.lower()}.{norm_name.lower().replace(' ', '_')}"
            ent_id = _compute_deterministic_hex_id(f"{ent_type.lower()}:{norm_name.lower()}")

            if ent_id not in discovered:
                discovered[ent_id] = Entity(
                    entity_id=ent_id,
                    entity_type=ent_type,
                    name=norm_name,
                    qualified_name=qualified,
                    location=source_location,
                    metadata={
                        "confidence": confidence,
                        "extraction_method": "rule_based",
                    },
                )

        # 1. Organizations
        for m in self._org_pattern.finditer(text):
            _add_entity("organization", m.group(1), confidence=0.92)

        # 2. Persons
        for m in self._person_pattern.finditer(text):
            _add_entity("person", m.group(1), confidence=0.90)

        # 3. Products
        for m in self._product_pattern.finditer(text):
            _add_entity("product", m.group(1), confidence=0.88)

        # 4. Locations
        for m in self._location_pattern.finditer(text):
            _add_entity("location", m.group(1), confidence=0.95)

        # 5. Concepts / Business terms
        if self.enable_concepts:
            for m in self._acronym_pattern.finditer(text):
                acronym = m.group(0)
                if acronym not in self._stop_words:
                    _add_entity("concept", acronym, confidence=0.85)

            for m in self._camel_concept_pattern.finditer(text):
                camel = m.group(0)
                if len(camel) >= 4 and camel not in self._stop_words:
                    _add_entity("concept", camel, confidence=0.85)

        return list(discovered.values())

    def extract_relationships(
        self,
        text: str,
        entities: List[Entity],
    ) -> List[Relationship]:
        """Extracts co-occurrence and semantic relationships among discovered entities."""
        if len(entities) < 2 or not text:
            return []

        relationships: List[Relationship] = []
        seen_edges: Set[Tuple[str, str, str]] = set()

        # Split text into sentences for localized co-occurrence
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

        for sentence in sentences:
            sentence_lower = sentence.lower()
            present_entities = [
                e for e in entities if e.name.lower() in sentence_lower
            ]

            if len(present_entities) < 2:
                continue

            # Check entity pairs in the same sentence
            for i in range(len(present_entities)):
                for j in range(i + 1, len(present_entities)):
                    e1 = present_entities[i]
                    e2 = present_entities[j]

                    if e1.entity_id == e2.entity_id:
                        continue

                    rel_type = "ASSOCIATED_WITH"
                    confidence = 0.85

                    # Semantic relation heuristics based on entity types
                    t1, t2 = e1.entity_type, e2.entity_type
                    if t1 == "person" and t2 == "organization":
                        rel_type = "AFFILIATED_WITH"
                        confidence = 0.90
                    elif t1 == "organization" and t2 == "person":
                        e1, e2 = e2, e1
                        rel_type = "AFFILIATED_WITH"
                        confidence = 0.90
                    elif t1 == "organization" and t2 == "product":
                        rel_type = "PRODUCES"
                        confidence = 0.88
                    elif t1 == "product" and t2 == "organization":
                        e1, e2 = e2, e1
                        rel_type = "PRODUCES"
                        confidence = 0.88
                    elif t1 == "organization" and t2 == "location":
                        rel_type = "OPERATES_IN"
                        confidence = 0.90
                    elif t1 == "location" and t2 == "organization":
                        e1, e2 = e2, e1
                        rel_type = "OPERATES_IN"
                        confidence = 0.90

                    edge_key = (e1.entity_id, rel_type, e2.entity_id)
                    if edge_key in seen_edges:
                        continue
                    seen_edges.add(edge_key)

                    rel_id = _compute_deterministic_hex_id(
                        f"{e1.entity_id}->{rel_type}->{e2.entity_id}"
                    )
                    relationships.append(Relationship(
                        relationship_id=rel_id,
                        source_entity_id=e1.entity_id,
                        target_entity_id=e2.entity_id,
                        relationship_type=rel_type,
                        confidence=confidence,
                        provenance={
                            "sentence_excerpt": sentence[:150],
                            "extraction_method": "rule_based_cooccurrence",
                        },
                    ))

        return relationships

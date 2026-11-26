from __future__ import annotations

"""Query Expander: Acronym Expansion, Domain Synonyms & Phrase Extraction.

Phase 1B/2A Implementation:
- Expands domain-specific abbreviations and acronyms with configurable domain vocabulary.
- Preserves exact quoted phrases ("AirFiber hold") and isolates them for phrase matching.
- Provides bidirectional terminology lookup:
  - AF <-> AirFiber
  - BIL <-> Business Internet Line
  - PV <-> Physical Verification
  - LoS <-> Line of Sight
  - UBR <-> User Based Router
  - Scheme <-> Payout / Commission / Incentive
  - Hold <-> Pending / Delay / Ticket
"""

import re
from typing import Dict, List, Set, Tuple


DEFAULT_ACRONYM_MAP: Dict[str, str] = {
    "af": "airfiber",
    "airfiber": "af",
    "bil": "business internet line",
    "business internet line": "bil",
    "pv": "physical verification",
    "physical verification": "pv",
    "los": "line of sight",
    "line of sight": "los",
    "ubr": "user based router",
    "user based router": "ubr",
    "sdu": "single dwelling unit",
    "mdu": "multi dwelling unit",
    "sla": "service level agreement",
}

DEFAULT_SYNONYM_MAP: Dict[str, List[str]] = {
    "scheme": ["payout", "commission", "incentive"],
    "hold": ["pending", "delay", "ticket", "blocker"],
    "installation": ["setup", "deployment", "provisioning"],
    "exception": ["hold", "error", "escalation", "deviation"],
}

QUOTED_PHRASE_PATTERN = re.compile(r'"([^"]+)"|\'([^\']+)\'')


class QueryExpander:
    """Configurable query expander with domain acronym and synonym dictionaries."""

    def __init__(
        self,
        acronym_map: Optional[Dict[str, str]] = None,
        synonym_map: Optional[Dict[str, List[str]]] = None,
        enable_acronyms: bool = True,
        enable_synonyms: bool = True,
    ) -> None:
        self.acronym_map: Dict[str, str] = dict(acronym_map or DEFAULT_ACRONYM_MAP)
        self.synonym_map: Dict[str, List[str]] = dict(synonym_map or DEFAULT_SYNONYM_MAP)
        self.enable_acronyms = enable_acronyms
        self.enable_synonyms = enable_synonyms

    def register_acronym(self, acronym: str, expansion: str) -> None:
        """Register or override a domain acronym mapping."""
        a = acronym.strip().lower()
        e = expansion.strip().lower()
        self.acronym_map[a] = e
        self.acronym_map[e] = a

    def register_synonyms(self, term: str, synonyms: List[str]) -> None:
        """Register or extend synonyms for a term."""
        t = term.strip().lower()
        clean_syns = [s.strip().lower() for s in synonyms if s.strip()]
        if t not in self.synonym_map:
            self.synonym_map[t] = []
        self.synonym_map[t].extend(clean_syns)

    def extract_exact_phrases(self, query: str) -> List[str]:
        """Extract explicit quoted phrases from the query."""
        if not query:
            return []
        matches = QUOTED_PHRASE_PATTERN.findall(query)
        phrases: List[str] = []
        for m in matches:
            phrase = m[0] or m[1]
            if phrase and phrase.strip():
                phrases.append(phrase.strip())
        return phrases

    def expand(self, query: str) -> str:
        """Expand search query with acronyms and domain synonyms."""
        if not query or not isinstance(query, str):
            return ""

        words = query.strip().split()
        expanded_tokens: List[str] = list(words)

        if self.enable_acronyms:
            for word in words:
                clean_w = re.sub(r"[^a-zA-Z0-9]", "", word).lower()
                if clean_w in self.acronym_map:
                    expansion = self.acronym_map[clean_w]
                    if expansion not in query.lower():
                        expanded_tokens.append(expansion)

        if self.enable_synonyms:
            for word in words:
                clean_w = re.sub(r"[^a-zA-Z0-9]", "", word).lower()
                if clean_w in self.synonym_map:
                    for syn in self.synonym_map[clean_w]:
                        if syn not in query.lower():
                            expanded_tokens.append(syn)

        return " ".join(expanded_tokens)

    def normalize(self, query: str) -> str:
        """Normalize punctuation and whitespace."""
        if not query:
            return ""
        cleaned = re.sub(r"[^\w\s\"'-]", " ", query)
        return " ".join(cleaned.split())

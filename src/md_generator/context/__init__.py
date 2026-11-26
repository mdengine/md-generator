from __future__ import annotations

"""Context Assembly & Evidence Validation Package.

Phase 1C/Prompt 04 Implementation:
- ContextManager: deterministic token-budgeted prompt synthesis with multi-tenant and document access isolation.
- ContextExpander: Small-to-Big retrieval (parent chunk expansion, sibling expansion).
- CitationManager: deterministic clickable citations (#page=N, #slide=N, #section=S, #Lstart-Lend) without fabrication.
- EvidenceValidator: citation grounding, hallucination detection, and conflict detection.
"""

from md_generator.context.citation import (
    Citation,
    CitationManager,
)
from md_generator.context.expander import (
    ContextExpander,
    ContextExpanderConfig,
    ParentExpansionMode,
)
from md_generator.context.manager import (
    AssembledContext,
    ContextManager,
    sanitize_untrusted_text,
    to_document_like,
)
from md_generator.context.validator import (
    EvidenceConflict,
    EvidenceValidationResult,
    EvidenceValidator,
)

__all__ = [
    # Citations
    "Citation",
    "CitationManager",
    # Context Expansion
    "ContextExpander",
    "ContextExpanderConfig",
    "ParentExpansionMode",
    # Context Assembly
    "AssembledContext",
    "ContextManager",
    "sanitize_untrusted_text",
    "to_document_like",
    # Evidence Validation
    "EvidenceConflict",
    "EvidenceValidationResult",
    "EvidenceValidator",
]

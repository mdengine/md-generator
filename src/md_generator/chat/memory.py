from __future__ import annotations

"""Conversation Memory, Reference Resolution & Topic Switch Detection.

Phase 2D/Prompt 06 Implementation:
- Resolves pronoun references ("it", "that document", "the previous result", "explain further").
- Tracks active topic, mentioned entities, and active document IDs across turns.
- Detects topic switching to prune stale history and avoid context poisoning.
"""

from dataclasses import dataclass, field
import re
from typing import Dict, List, Optional, Set, Tuple

from md_generator.chat.models import ChatMessage, ChatSession, MessageRole


REFERENCE_PRONOUNS_PATTERN = re.compile(
    r"\b(it|this|that|these|those|them|its|the previous result|that document|explain further|tell me more|more details|elaborate)\b",
    re.IGNORECASE
)


class ConversationMemory:
    """Manages conversational continuity, entity tracking, and coreference resolution."""

    def __init__(
        self,
        max_tracked_entities: int = 10,
        topic_switch_overlap_threshold: float = 0.15,
    ) -> None:
        self.max_tracked_entities = max_tracked_entities
        self.topic_switch_overlap_threshold = topic_switch_overlap_threshold

    def extract_query_keywords(self, text: str) -> Set[str]:
        """Extracts significant semantic keywords from user query."""
        words = re.findall(r"\b[A-Za-z0-9_-]{3,}\b", text.lower())
        stop_words = {
            "what", "where", "when", "which", "who", "whom", "whose", "why", "how",
            "the", "and", "for", "with", "from", "that", "this", "can", "you", "tell",
            "more", "about", "please", "show", "explain", "give", "does", "have", "been"
        }
        return {w for w in words if w not in stop_words}

    def detect_topic_switch(
        self,
        current_query: str,
        session: ChatSession,
    ) -> bool:
        """Detects whether current query initiates a new topic compared to recent turns."""
        if not session.messages:
            return False

        # If query contains explicit reference pronouns, it is continuing the topic
        if REFERENCE_PRONOUNS_PATTERN.search(current_query):
            return False

        current_keywords = self.extract_query_keywords(current_query)
        if not current_keywords:
            return False

        # Compare with recent user turns (last 2 turns)
        recent_user_msgs = [m for m in session.messages if m.role == MessageRole.USER][-2:]
        if not recent_user_msgs:
            return False

        recent_keywords: Set[str] = set()
        for m in recent_user_msgs:
            recent_keywords.update(self.extract_query_keywords(m.content))

        if not recent_keywords:
            return False

        overlap = len(current_keywords.intersection(recent_keywords))
        overlap_ratio = overlap / max(1, len(current_keywords))

        return overlap_ratio < self.topic_switch_overlap_threshold

    def resolve_references(
        self,
        query: str,
        session: ChatSession,
    ) -> Tuple[str, List[str]]:
        """Resolves references ('it', 'that document') using previous turn context.
        
        Returns:
            Tuple[str, List[str]]: (reformulated_query, list_of_resolved_references)
        """
        if not session.messages:
            return query, []

        resolved_refs: List[str] = []
        clean_q = query.strip()

        # Check for reference markers
        has_pronoun = bool(REFERENCE_PRONOUNS_PATTERN.search(clean_q))
        if not has_pronoun:
            return clean_q, []

        # Find last assistant message and last user message
        last_user_msg = next((m for m in reversed(session.messages) if m.role == MessageRole.USER), None)
        last_asst_msg = next((m for m in reversed(session.messages) if m.role == MessageRole.ASSISTANT), None)

        antecedent_entity = ""
        # 1. Check tracked entities
        if session.tracked_entities:
            # Pick most recently updated tracked entity
            antecedent_entity = list(session.tracked_entities.values())[-1]

        # 2. Check last user query keywords
        if not antecedent_entity and last_user_msg:
            user_kw = self.extract_query_keywords(last_user_msg.content)
            if user_kw:
                antecedent_entity = " ".join(list(user_kw)[:2])

        # 3. Check citations from last assistant turn
        antecedent_doc = ""
        if last_asst_msg and last_asst_msg.citations:
            top_cit = last_asst_msg.citations[0]
            antecedent_doc = top_cit.document_id

        reformulated = clean_q
        if antecedent_entity:
            # Append contextual clarifier to search query
            reformulated = f"{clean_q} (regarding {antecedent_entity})"
            resolved_refs.append(f"Entity: {antecedent_entity}")

        if "that document" in clean_q.lower() and antecedent_doc:
            reformulated = reformulated.replace("that document", f"document {antecedent_doc}")
            resolved_refs.append(f"Document: {antecedent_doc}")

        return reformulated, resolved_refs

    def update_session_memory(
        self,
        session: ChatSession,
        query: str,
        answer: str,
        citations: List[Any],
    ) -> None:
        """Updates tracked entities, active documents, and topic in session memory."""
        # 1. Update active document IDs from citations
        for cit in citations:
            doc_id = getattr(cit, "document_id", None)
            if doc_id:
                session.active_document_ids.add(str(doc_id))

        # 2. Extract entities from query and answer
        keywords = self.extract_query_keywords(query)
        for kw in keywords:
            if len(session.tracked_entities) < self.max_tracked_entities:
                session.tracked_entities[kw] = kw

        # 3. Update active topic
        if not session.active_topic:
            session.active_topic = query[:60].strip()
        elif self.detect_topic_switch(query, session):
            session.active_topic = query[:60].strip()
            # Clear older entities on topic switch
            session.tracked_entities = {kw: kw for kw in list(keywords)[:3]}

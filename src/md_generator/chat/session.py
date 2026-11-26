from __future__ import annotations

"""Session Storage & Multi-tenant Conversation Management.

Phase 2D/Prompt 06 Implementation:
- Abstract BaseSessionStore interface.
- InMemorySessionStore with multi-tenant partitioning, thread-safety, and expiration.
- FileSessionStore for persistent offline JSON sessions.
"""

from abc import ABC, abstractmethod
import copy
import json
from pathlib import Path
import threading
import time
from typing import Any, Dict, List, Optional
import uuid

from md_generator.chat.models import ChatSession, ChatMessage
from md_generator.graph.model import _validate_tenant_id
from md_generator.graph.exceptions import TenantBoundaryError


class BaseSessionStore(ABC):
    """Abstract interface for chat session persistence."""

    @abstractmethod
    def create_session(self, session: ChatSession) -> ChatSession:
        pass

    @abstractmethod
    def get_session(self, session_id: str, tenant_id: str) -> Optional[ChatSession]:
        pass

    @abstractmethod
    def update_session(self, session: ChatSession, touch: bool = True) -> None:
        pass

    @abstractmethod
    def delete_session(self, session_id: str, tenant_id: str) -> bool:
        pass

    @abstractmethod
    def list_sessions(self, tenant_id: str, user_id: Optional[str] = None) -> List[ChatSession]:
        pass

    @abstractmethod
    def cleanup_expired_sessions(self, max_age_seconds: float) -> int:
        pass


class InMemorySessionStore(BaseSessionStore):
    """Thread-safe in-memory session store partitioned strictly by tenant."""

    def __init__(self) -> None:
        # tenant_id -> session_id -> ChatSession
        self._sessions: Dict[str, Dict[str, ChatSession]] = {}
        # tenant_id -> conversation_id -> session_id
        self._conv_index: Dict[str, Dict[str, str]] = {}
        self._lock = threading.RLock()

    def create_session(self, session: ChatSession) -> ChatSession:
        clean_tenant = _validate_tenant_id(session.tenant_id, "InMemorySessionStore.create_session.tenant_id")
        with self._lock:
            if clean_tenant not in self._sessions:
                self._sessions[clean_tenant] = {}
                self._conv_index[clean_tenant] = {}

            if not session.session_id:
                session.session_id = f"sess_{uuid.uuid4().hex[:16]}"
            if not session.conversation_id:
                session.conversation_id = f"conv_{uuid.uuid4().hex[:16]}"

            session.updated_at = time.time()
            self._sessions[clean_tenant][session.session_id] = copy.deepcopy(session)
            self._conv_index[clean_tenant][session.conversation_id] = session.session_id
            return copy.deepcopy(session)

    def get_session(self, session_id: str, tenant_id: str) -> Optional[ChatSession]:
        clean_tenant = _validate_tenant_id(tenant_id, "InMemorySessionStore.get_session.tenant_id")
        with self._lock:
            sess = self._sessions.get(clean_tenant, {}).get(session_id)
            return copy.deepcopy(sess) if sess is not None else None

    def get_session_by_conversation(self, conversation_id: str, tenant_id: str) -> Optional[ChatSession]:
        clean_tenant = _validate_tenant_id(tenant_id, "InMemorySessionStore.get_session_by_conversation.tenant_id")
        with self._lock:
            sess_id = self._conv_index.get(clean_tenant, {}).get(conversation_id)
            if not sess_id:
                return None
            return self.get_session(sess_id, clean_tenant)

    def create_or_get_session(
        self,
        conversation_id: Optional[str],
        session_id: Optional[str],
        tenant_id: str,
        user_id: str = "default_user",
    ) -> ChatSession:
        """Finds existing session or instantiates a fresh session."""
        clean_tenant = _validate_tenant_id(tenant_id, "InMemorySessionStore.create_or_get_session.tenant_id")
        with self._lock:
            if session_id:
                existing = self.get_session(session_id, clean_tenant)
                if existing:
                    return existing

            if conversation_id:
                existing = self.get_session_by_conversation(conversation_id, clean_tenant)
                if existing:
                    return existing

            new_sess = ChatSession(
                session_id=session_id or f"sess_{uuid.uuid4().hex[:16]}",
                conversation_id=conversation_id or f"conv_{uuid.uuid4().hex[:16]}",
                tenant_id=clean_tenant,
                user_id=user_id,
                created_at=time.time(),
                updated_at=time.time(),
            )
            return self.create_session(new_sess)

    def update_session(self, session: ChatSession, touch: bool = True) -> None:
        clean_tenant = _validate_tenant_id(session.tenant_id, "InMemorySessionStore.update_session.tenant_id")
        with self._lock:
            if clean_tenant not in self._sessions or session.session_id not in self._sessions[clean_tenant]:
                raise KeyError(f"Session '{session.session_id}' does not exist for tenant '{clean_tenant}'.")
            if touch:
                session.updated_at = time.time()
            self._sessions[clean_tenant][session.session_id] = copy.deepcopy(session)
            self._conv_index[clean_tenant][session.conversation_id] = session.session_id

    def delete_session(self, session_id: str, tenant_id: str) -> bool:
        clean_tenant = _validate_tenant_id(tenant_id, "InMemorySessionStore.delete_session.tenant_id")
        with self._lock:
            if clean_tenant in self._sessions and session_id in self._sessions[clean_tenant]:
                sess = self._sessions[clean_tenant].pop(session_id)
                self._conv_index.get(clean_tenant, {}).pop(sess.conversation_id, None)
                return True
            return False

    def list_sessions(self, tenant_id: str, user_id: Optional[str] = None) -> List[ChatSession]:
        clean_tenant = _validate_tenant_id(tenant_id, "InMemorySessionStore.list_sessions.tenant_id")
        with self._lock:
            sessions = list(self._sessions.get(clean_tenant, {}).values())
            if user_id:
                sessions = [s for s in sessions if s.user_id == user_id]
            # Sorted by updated_at descending
            sessions.sort(key=lambda s: -s.updated_at)
            return [copy.deepcopy(s) for s in sessions]

    def cleanup_expired_sessions(self, max_age_seconds: float) -> int:
        now = time.time()
        purged = 0
        with self._lock:
            for tenant, sessions in list(self._sessions.items()):
                to_delete = [
                    sid for sid, s in sessions.items()
                    if now - s.updated_at > max_age_seconds
                ]
                for sid in to_delete:
                    sess = sessions.pop(sid)
                    self._conv_index.get(tenant, {}).pop(sess.conversation_id, None)
                    purged += 1
        return purged


class FileSessionStore(BaseSessionStore):
    """Persistent filesystem session store storing JSON files per tenant."""

    def __init__(self, base_dir: Path | str) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _tenant_dir(self, tenant_id: str) -> Path:
        clean_tenant = _validate_tenant_id(tenant_id, "FileSessionStore._tenant_dir.tenant_id")
        tdir = self.base_dir / clean_tenant
        tdir.mkdir(parents=True, exist_ok=True)
        return tdir

    def create_session(self, session: ChatSession) -> ChatSession:
        clean_tenant = _validate_tenant_id(session.tenant_id, "FileSessionStore.create_session.tenant_id")
        with self._lock:
            if not session.session_id:
                session.session_id = f"sess_{uuid.uuid4().hex[:16]}"
            if not session.conversation_id:
                session.conversation_id = f"conv_{uuid.uuid4().hex[:16]}"
            session.updated_at = time.time()

            file_path = self._tenant_dir(clean_tenant) / f"{session.session_id}.json"
            tmp_file = self._tenant_dir(clean_tenant) / f"{session.session_id}.json.tmp"
            tmp_file.write_text(json.dumps(session.to_dict(), indent=2), encoding="utf-8")
            tmp_file.replace(file_path)
            return copy.deepcopy(session)

    def get_session(self, session_id: str, tenant_id: str) -> Optional[ChatSession]:
        clean_tenant = _validate_tenant_id(tenant_id, "FileSessionStore.get_session.tenant_id")
        with self._lock:
            file_path = self._tenant_dir(clean_tenant) / f"{session_id}.json"
            if not file_path.exists():
                return None
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                return ChatSession.from_dict(data)
            except Exception:
                return None

    def update_session(self, session: ChatSession, touch: bool = True) -> None:
        clean_tenant = _validate_tenant_id(session.tenant_id, "FileSessionStore.update_session.tenant_id")
        with self._lock:
            file_path = self._tenant_dir(clean_tenant) / f"{session.session_id}.json"
            if not file_path.exists():
                raise KeyError(f"Session '{session.session_id}' not found.")
            if touch:
                session.updated_at = time.time()
            tmp_file = self._tenant_dir(clean_tenant) / f"{session.session_id}.json.tmp"
            tmp_file.write_text(json.dumps(session.to_dict(), indent=2), encoding="utf-8")
            tmp_file.replace(file_path)

    def delete_session(self, session_id: str, tenant_id: str) -> bool:
        clean_tenant = _validate_tenant_id(tenant_id, "FileSessionStore.delete_session.tenant_id")
        with self._lock:
            file_path = self._tenant_dir(clean_tenant) / f"{session_id}.json"
            if file_path.exists():
                file_path.unlink()
                return True
            return False

    def list_sessions(self, tenant_id: str, user_id: Optional[str] = None) -> List[ChatSession]:
        clean_tenant = _validate_tenant_id(tenant_id, "FileSessionStore.list_sessions.tenant_id")
        with self._lock:
            tdir = self._tenant_dir(clean_tenant)
            sessions: List[ChatSession] = []
            for f in tdir.glob("*.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    sess = ChatSession.from_dict(data)
                    if user_id is None or sess.user_id == user_id:
                        sessions.append(sess)
                except Exception:
                    continue
            sessions.sort(key=lambda s: -s.updated_at)
            return sessions

    def cleanup_expired_sessions(self, max_age_seconds: float) -> int:
        now = time.time()
        purged = 0
        with self._lock:
            for f in self.base_dir.rglob("*.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    updated_at = float(data.get("updated_at", 0))
                    if now - updated_at > max_age_seconds:
                        f.unlink()
                        purged += 1
                except Exception:
                    continue
        return purged

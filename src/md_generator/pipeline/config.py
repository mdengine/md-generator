from __future__ import annotations

"""PipelineConfig & Deterministic Configuration Fingerprint.

Phase 0C-1 Implementation: Config model, tenant boundary isolation,
and canonical metadata fingerprint calculation.
"""

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Dict, Optional

from md_generator.lineage.manifest import VersionedManifest
from md_generator.security.policy import SecurityPolicy


@dataclass
class PipelineConfig:
    """Logical configuration for an MDPipeline execution run."""

    tenant: str = "default"
    security_policy: SecurityPolicy = field(default_factory=SecurityPolicy)
    enable_delta_sync: bool = True
    manifest: Optional[VersionedManifest] = None
    repository: str = ""
    commit: str = ""
    extra_metadata: Dict[str, Any] = field(default_factory=dict)

    def compute_fingerprint(self) -> str:
        """Compute deterministic SHA-256 fingerprint for logical processing configuration."""
        canonical_extra = self._canonicalize_extra_metadata(self.extra_metadata)
        sec_policy_dict = (
            self.security_policy.to_dict()
            if hasattr(self.security_policy, "to_dict")
            else dict(self.security_policy)
        )
        data = {
            "commit": self.commit.strip(),
            "extra_metadata": canonical_extra,
            "repository": self.repository.strip(),
            "security_policy": sec_policy_dict,
            "tenant": self.tenant.strip(),
        }
        raw_json = json.dumps(
            data, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        return hashlib.sha256(raw_json.encode("utf-8")).hexdigest()

    @classmethod
    def _canonicalize_extra_metadata(cls, obj: Any) -> Any:
        """Recursively canonicalize metadata values for deterministic hashing."""
        if isinstance(obj, dict):
            return {
                str(k): cls._canonicalize_extra_metadata(v)
                for k, v in sorted(obj.items(), key=lambda item: str(item[0]))
            }
        elif isinstance(obj, (set, frozenset)):
            return [cls._canonicalize_extra_metadata(item) for item in sorted(obj, key=str)]
        elif isinstance(obj, (list, tuple)):
            return [cls._canonicalize_extra_metadata(item) for item in obj]
        elif hasattr(obj, "to_dict") and callable(obj.to_dict):
            return cls._canonicalize_extra_metadata(obj.to_dict())
        return obj

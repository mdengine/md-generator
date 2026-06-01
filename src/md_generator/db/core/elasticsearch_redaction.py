"""Sensitive value redaction for Elasticsearch export markdown."""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field, replace
from typing import Any

from md_generator.db.core.models import (
    ElasticsearchComponentTemplateInfo,
    ElasticsearchDataStreamInfo,
    ElasticsearchIndexInfo,
    ElasticsearchIndexTemplateInfo,
    ElasticsearchIlmPolicyInfo,
    ElasticsearchPipelineInfo,
    ElasticsearchSearchTemplateInfo,
    ElasticsearchSlmPolicyInfo,
    ElasticsearchSnapshotRepositoryInfo,
)

DEFAULT_REDACT_PATTERNS: tuple[str, ...] = (
    "password",
    "secret",
    "token",
    "api_key",
    "access_key",
    "authorization",
)

_EMBEDDED_CRED_URL = re.compile(r"://([^/@]+):([^/@]+)@")


@dataclass(frozen=True)
class RedactionConfig:
    enabled: bool = False
    patterns: tuple[str, ...] = DEFAULT_REDACT_PATTERNS

    def normalized(self) -> RedactionConfig:
        patterns = self.patterns or DEFAULT_REDACT_PATTERNS
        cleaned = tuple(str(p).strip().lower() for p in patterns if str(p).strip())
        return RedactionConfig(
            enabled=bool(self.enabled),
            patterns=cleaned or DEFAULT_REDACT_PATTERNS,
        )


@dataclass
class RedactionAudit:
    matched_patterns: set[str] = field(default_factory=set)

    @property
    def applied(self) -> bool:
        return bool(self.matched_patterns)

    def merge(self, patterns: frozenset[str]) -> None:
        self.matched_patterns.update(patterns)

    def to_manifest_dict(self) -> dict[str, Any]:
        return {
            "applied": self.applied,
            "redacted_keys": sorted(self.matched_patterns),
        }


def redaction_config_from_dict(raw: dict[str, Any] | None) -> RedactionConfig:
    if not isinstance(raw, dict):
        return RedactionConfig().normalized()
    patterns_raw = raw.get("redact_patterns")
    patterns: tuple[str, ...] = DEFAULT_REDACT_PATTERNS
    if isinstance(patterns_raw, list):
        patterns = tuple(str(x) for x in patterns_raw if str(x).strip())
    elif isinstance(patterns_raw, str):
        patterns = tuple(x.strip() for x in patterns_raw.split(",") if x.strip())
    enabled = raw.get("redact_sensitive_values", False)
    if isinstance(enabled, str):
        enabled = enabled.lower() not in ("false", "0", "no")
    return RedactionConfig(enabled=bool(enabled), patterns=patterns).normalized()


def _matching_pattern(key: str, patterns: tuple[str, ...]) -> str | None:
    key_lower = key.lower()
    for pattern in patterns:
        if pattern in key_lower:
            return pattern
    return None


def _redact_string(value: str) -> tuple[str, frozenset[str]]:
    if _EMBEDDED_CRED_URL.search(value):
        return (
            _EMBEDDED_CRED_URL.sub("://[REDACTED]:[REDACTED]@", value),
            frozenset({"authorization"}),
        )
    return value, frozenset()


def redact_structure(obj: Any, config: RedactionConfig) -> tuple[Any, frozenset[str]]:
    cfg = config.normalized()
    if not cfg.enabled:
        return obj, frozenset()
    matched: set[str] = set()

    def walk(value: Any) -> Any:
        if isinstance(value, dict):
            out: dict[str, Any] = {}
            for key, item in value.items():
                pattern = _matching_pattern(str(key), cfg.patterns)
                if pattern is not None and item is not None:
                    matched.add(pattern)
                    out[key] = "[REDACTED]"
                else:
                    out[key] = walk(item)
            return out
        if isinstance(value, list):
            return [walk(item) for item in value]
        if isinstance(value, str):
            redacted, pats = _redact_string(value)
            matched.update(pats)
            return redacted
        return value

    return walk(copy.deepcopy(obj)), frozenset(matched)


def _merge_patterns(*groups: frozenset[str]) -> frozenset[str]:
    out: set[str] = set()
    for group in groups:
        out.update(group)
    return frozenset(out)


def redact_elasticsearch_entity(
    entity: Any,
    config: RedactionConfig,
) -> tuple[Any, frozenset[str]]:
    cfg = config.normalized()
    if not cfg.enabled:
        return entity, frozenset()

    if isinstance(entity, ElasticsearchIndexInfo):
        mappings, p1 = redact_structure(entity.mappings, cfg)
        settings, p2 = redact_structure(entity.settings, cfg)
        shard_config, p3 = redact_structure(entity.shard_config, cfg)
        field_caps = entity.field_caps
        p4 = frozenset()
        if field_caps is not None:
            field_caps, p4 = redact_structure(field_caps, cfg)
        return (
            replace(
                entity,
                mappings=mappings,
                settings=settings,
                shard_config=shard_config,
                field_caps=field_caps,
            ),
            _merge_patterns(p1, p2, p3, p4),
        )

    if isinstance(entity, ElasticsearchDataStreamInfo):
        definition, p = redact_structure(entity.definition, cfg)
        return replace(entity, definition=definition), p

    if isinstance(entity, ElasticsearchComponentTemplateInfo):
        template, p = redact_structure(entity.template, cfg)
        return replace(entity, template=template), p

    if isinstance(entity, ElasticsearchPipelineInfo):
        definition, p = redact_structure(entity.definition, cfg)
        return replace(entity, definition=definition), p

    if isinstance(entity, ElasticsearchIndexTemplateInfo):
        template, p = redact_structure(entity.template, cfg)
        return replace(entity, template=template), p

    if isinstance(entity, ElasticsearchIlmPolicyInfo):
        policy, p = redact_structure(entity.policy, cfg)
        return replace(entity, policy=policy), p

    if isinstance(entity, ElasticsearchSlmPolicyInfo):
        policy, p = redact_structure(entity.policy, cfg)
        return replace(entity, policy=policy), p

    if isinstance(entity, ElasticsearchSnapshotRepositoryInfo):
        settings, p1 = redact_structure(entity.settings, cfg)
        operational, p2 = redact_structure(entity.operational, cfg)
        return (
            replace(entity, settings=settings, operational=operational),
            _merge_patterns(p1, p2),
        )

    if isinstance(entity, ElasticsearchSearchTemplateInfo):
        definition, p1 = redact_structure(entity.definition, cfg)
        preview = entity.source_preview
        p2 = frozenset()
        if preview is not None:
            preview, p2 = redact_structure(preview, cfg)
        return (
            replace(entity, definition=definition, source_preview=preview),
            _merge_patterns(p1, p2),
        )

    return entity, frozenset()

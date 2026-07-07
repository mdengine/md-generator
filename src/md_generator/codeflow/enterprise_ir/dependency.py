from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from md_generator.codeflow.enterprise_ir.base import BaseEntity

DependencyType = Literal[
    "Internal Module",
    "External Library",
    "Framework",
    "SDK",
    "Cloud SDK",
    "Plugin",
    "Runtime Library",
]


@dataclass
class DependencyEntity(BaseEntity):
    name: str
    version: str
    language_key: str
    scope: str
    group: str | None = None
    artifact: str | None = None
    dependency_type: DependencyType = "External Library"
    license_name: str | None = None
    repo_url: str | None = None
    is_optional: bool = False
    is_transitive: bool = False
    usage_files: list[str] = field(default_factory=list)
    usage_methods: list[str] = field(default_factory=list)
    usage_frequency: int = 0

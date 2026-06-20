from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from md_generator.codeflow.enterprise_ir.base import PluginCategory
from md_generator.codeflow.enterprise_ir.graph import EnterpriseIR
from md_generator.codeflow.repository.model import Repository


@dataclass
class PluginMetadata:
    name: str
    category: PluginCategory
    supported_languages: list[str] = field(default_factory=list)
    supported_extensions: list[str] = field(default_factory=list)
    supports_cfg: bool = False
    supports_runtime: bool = False
    supports_incremental: bool = False
    priority: int = 10
    depends_on: list[str] = field(default_factory=list)


class BasePlugin(ABC):
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Returns metadata for the plugin."""
        ...

    @abstractmethod
    def discover(self, repository: Repository) -> list[Path]:
        """Locates source files in the workspace targeting this plugin."""
        ...

    @abstractmethod
    def scan(self, file_path: Path) -> bool:
        """Verifies access to the file and checks if scanning is required."""
        ...

    @abstractmethod
    def extract(self, file_path: Path) -> Any:
        """Extracts language elements and statements from the file."""
        ...

    @abstractmethod
    def normalize(self, raw_payload: Any) -> Any:
        """Normalizes extracted raw elements to a common data model."""
        ...

    @abstractmethod
    def validate(self, normalized_data: Any) -> bool:
        """Validates that the normalized data matches constraints."""
        ...

    @abstractmethod
    def post_process(self, normalized_data: Any) -> Any:
        """Applies optimizations or cleanups on the normalized records."""
        ...

    @abstractmethod
    def build_ir(self, normalized_data: Any) -> EnterpriseIR:
        """Maps normalized records to the canonical EnterpriseIR."""
        ...

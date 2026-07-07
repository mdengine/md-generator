from __future__ import annotations

from pathlib import Path
from typing import Any

from md_generator.codeflow.enterprise_ir.base import PluginCategory
from md_generator.codeflow.enterprise_ir.graph import EnterpriseIR
from md_generator.codeflow.plugins.base import BasePlugin, PluginMetadata
from md_generator.codeflow.repository.model import Repository


class SemanticPlugin(BasePlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="semantic_plugin",
            category=PluginCategory.ANALYZER,
            supported_languages=["python", "java", "javascript", "typescript", "go", "php"],
            supported_extensions=[".py", ".java", ".js", ".ts", ".go", ".php"],
        )

    def discover(self, repository: Repository) -> list[Path]:
        return []

    def scan(self, file_path: Path) -> bool:
        return False

    def extract(self, file_path: Path) -> Any:
        return {}

    def normalize(self, raw_payload: Any) -> Any:
        return {}

    def validate(self, normalized_data: Any) -> bool:
        return True

    def post_process(self, normalized_data: Any) -> Any:
        return normalized_data

    def build_ir(self, normalized_data: Any) -> EnterpriseIR:
        return EnterpriseIR()

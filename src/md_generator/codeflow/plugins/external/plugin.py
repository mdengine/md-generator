from __future__ import annotations

from pathlib import Path
from typing import Any

from md_generator.codeflow.adapters import global_registry
from md_generator.codeflow.enterprise_ir.base import NodeMetadata, NodeType, PluginCategory
from md_generator.codeflow.enterprise_ir.graph import EnterpriseIR
from md_generator.codeflow.enterprise_ir.resource import ResourceEntity
from md_generator.codeflow.plugins.base import BasePlugin, PluginMetadata
from md_generator.codeflow.repository.model import Repository


class ExternalPlugin(BasePlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="external",
            category=PluginCategory.PARSER,
            supported_languages=["python", "java", "javascript", "typescript", "go", "php"],
            supported_extensions=[".py", ".java", ".js", ".ts", ".go", ".php"],
        )

    def discover(self, repository: Repository) -> list[Path]:
        res = []
        for ext in self.metadata.supported_extensions:
            res.extend(repository.path.rglob(f"*{ext}"))
        return sorted(res)

    def scan(self, file_path: Path) -> bool:
        return file_path.exists() and file_path.is_file()

    def extract(self, file_path: Path) -> Any:
        adapter = global_registry.get_adapter_for_path(file_path)
        if not adapter:
            return []
        backend = global_registry.select_backend(adapter)
        return adapter.extract_external_resources(file_path, backend)

    def normalize(self, raw_payload: Any) -> Any:
        return raw_payload

    def validate(self, normalized_data: Any) -> bool:
        return isinstance(normalized_data, list)

    def post_process(self, normalized_data: Any) -> Any:
        return normalized_data

    def build_ir(self, normalized_data: Any) -> EnterpriseIR:
        ir = EnterpriseIR()
        repo_name = "local"
        for rd in normalized_data:
            meta = NodeMetadata(
                id=rd.uri,
                kind=NodeType.RESOURCE,
                language="mixed",
                repository=repo_name,
                module=None,
                file="",
                line=0,
                column=0,
                confidence="MEDIUM",
                parser="external_plugin",
                backend="native",
            )
            ir.resources.append(
                ResourceEntity(
                    id=rd.uri,
                    metadata=meta,
                    resource_type=rd.resource_type,
                    uri=rd.uri,
                )
            )
        return ir

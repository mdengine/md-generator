from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any

from md_generator.codeflow.adapters import global_registry
from md_generator.codeflow.enterprise_ir.base import NodeMetadata, NodeType, PluginCategory
from md_generator.codeflow.enterprise_ir.dependency import DependencyEntity, DependencyType
from md_generator.codeflow.enterprise_ir.graph import EnterpriseIR
from md_generator.codeflow.plugins.base import BasePlugin, PluginMetadata
from md_generator.codeflow.repository.model import Repository


class DependencyPlugin(BasePlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="dependency",
            category=PluginCategory.PARSER,
            supported_languages=["java", "javascript", "typescript", "python", "go", "php"],
            supported_extensions=["pom.xml", "package.json", "requirements.txt", "go.mod", "composer.json"],
        )

    def discover(self, repository: Repository) -> list[Path]:
        res = []
        for name in self.metadata.supported_extensions:
            res.extend(repository.path.rglob(name))
        return sorted(res)

    def scan(self, file_path: Path) -> bool:
        return file_path.exists() and file_path.is_file()

    def extract(self, file_path: Path) -> Any:
        adapter = global_registry.get_adapter_for_path(file_path)
        if not adapter:
            return []
        backend = global_registry.select_backend(adapter)
        return adapter.extract_dependencies(file_path, backend)

    def normalize(self, raw_payload: Any) -> Any:
        return raw_payload

    def validate(self, normalized_data: Any) -> bool:
        return isinstance(normalized_data, list)

    def post_process(self, normalized_data: Any) -> Any:
        # Load classification rules from codeflow.yaml if present
        rules = {}
        cf_yaml = Path("codeflow.yaml")
        if cf_yaml.exists():
            try:
                cf_data = yaml.safe_load(cf_yaml.read_text(encoding="utf-8"))
                rules = cf_data.get("dependency-classification", {})
            except Exception:
                pass
        
        # Apply classifications e.g. SDK, Framework, Internal Module
        for dep in normalized_data:
            name = dep.name
            dtype: DependencyType = "External Library"
            
            # Match user regex rules
            matched = False
            for cat, patterns in rules.items():
                for pat in patterns:
                    import re
                    if re.match(pat, name):
                        if cat == "framework":
                            dtype = "Framework"
                        elif cat == "cloud-sdk":
                            dtype = "Cloud SDK"
                        elif cat == "internal":
                            dtype = "Internal Module"
                        matched = True
                        break
                if matched:
                    break
            
            # Default fallbacks
            if not matched:
                if "spring" in name or "django" in name or "express" in name:
                    dtype = "Framework"
                elif "aws" in name or "azure" in name or "google" in name or "sdk" in name:
                    dtype = "Cloud SDK"
            
            dep.dependency_type = dtype
        return normalized_data

    def build_ir(self, normalized_data: Any) -> EnterpriseIR:
        ir = EnterpriseIR()
        for rd in normalized_data:
            dep_id = f"dependency://{rd.name}"
            meta = NodeMetadata(
                id=dep_id,
                kind=NodeType.DEPENDENCY,
                language="mixed",
                repository="local",
                module=None,
                file="",
                line=0,
                column=0,
                confidence="HIGH",
                parser="dependency_plugin",
                backend="native",
            )
            ir.dependencies.append(
                DependencyEntity(
                    id=dep_id,
                    metadata=meta,
                    name=rd.name,
                    version=rd.version,
                    language_key="mixed",
                    scope=rd.scope,
                    group=rd.group,
                    artifact=rd.artifact,
                    dependency_type=getattr(rd, "dependency_type", "External Library"),
                    license_name=rd.license_name,
                    repo_url=rd.repo_url,
                    is_optional=rd.optional,
                    is_transitive=rd.transitive,
                )
            )
        return ir

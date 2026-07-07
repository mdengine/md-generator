from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from md_generator.codeflow.adapters.base import (
    ConfigUsage,
    ImportRecord,
    LanguageAdapter,
    RawDependency,
    RawEvent,
    RawQuery,
    RawResource,
    SymbolRecord,
)
from md_generator.codeflow.enterprise_ir.base import NodeMetadata, NodeType
from md_generator.codeflow.enterprise_ir.config import ConfigEntity
from md_generator.codeflow.enterprise_ir.dependency import DependencyEntity
from md_generator.codeflow.enterprise_ir.graph import EnterpriseIR


class JavaScriptAdapter(LanguageAdapter):
    @property
    def language(self) -> str:
        return "javascript"

    @property
    def supported_extensions(self) -> list[str]:
        return [".js", ".jsx", ".mjs", ".cjs"]

    @property
    def parser_backends(self) -> list[str]:
        return ["treesitter", "regex"]

    def discover(self, workspace_root: Path) -> list[Path]:
        return sorted(list(workspace_root.rglob("*.js")) + list(workspace_root.rglob("package.json")))

    def extract_symbols(self, file_path: Path, backend: str) -> list[SymbolRecord]:
        return []

    def extract_imports(self, file_path: Path, backend: str) -> list[ImportRecord]:
        return []

    def extract_dependencies(self, file_path: Path, backend: str) -> list[RawDependency]:
        deps: list[RawDependency] = []
        if file_path.name == "package.json":
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                for k in ["dependencies", "devDependencies"]:
                    if k in data:
                        for name, ver in data[k].items():
                            deps.append(
                                RawDependency(
                                    name=name,
                                    version=ver,
                                    scope="compile" if k == "dependencies" else "dev",
                                )
                            )
            except Exception:
                pass
        return deps

    def extract_config_usage(self, file_path: Path, backend: str) -> list[ConfigUsage]:
        usages: list[ConfigUsage] = []
        if file_path.suffix.lower() not in self.supported_extensions:
            return usages
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            matches = re.finditer(r"process\.env\.([a-zA-Z0-9_]+)", content)
            for m in matches:
                key = m.group(1)
                line_num = content.count("\n", 0, m.start()) + 1
                usages.append(
                    ConfigUsage(
                        key=key,
                        source_file=str(file_path),
                        line=line_num,
                        usage_type="Env",
                    )
                )
        except Exception:
            pass
        return usages

    def extract_queries(self, file_path: Path, backend: str) -> list[RawQuery]:
        return []

    def extract_external_resources(self, file_path: Path, backend: str) -> list[RawResource]:
        return []

    def extract_events(self, file_path: Path, backend: str) -> list[RawEvent]:
        return []

    def build_ir(self, file_path: Path, backend: str, extracted_data: dict[str, Any]) -> EnterpriseIR:
        ir = EnterpriseIR()
        repo_name = "local"
        
        # Populate configs
        for cu in extracted_data.get("configs", []):
            meta = NodeMetadata(
                id=f"config://{cu.key}",
                kind=NodeType.CONFIG,
                language=self.language,
                repository=repo_name,
                module=None,
                file=str(file_path),
                line=cu.line,
                column=0,
                confidence="HIGH",
                parser="js_adapter",
                backend=backend,
            )
            ir.configs.append(
                ConfigEntity(
                    id=f"config://{cu.key}",
                    metadata=meta,
                    key=cu.key,
                    value="",
                    type_name="string",
                    source=str(file_path),
                    line=cu.line,
                )
            )

        # Populate dependencies
        for rd in extracted_data.get("dependencies", []):
            dep_id = f"dependency://{rd.name}"
            meta = NodeMetadata(
                id=dep_id,
                kind=NodeType.DEPENDENCY,
                language=self.language,
                repository=repo_name,
                module=None,
                file=str(file_path),
                line=0,
                column=0,
                confidence="HIGH",
                parser="js_adapter",
                backend=backend,
            )
            ir.dependencies.append(
                DependencyEntity(
                    id=dep_id,
                    metadata=meta,
                    name=rd.name,
                    version=rd.version,
                    language_key=self.language,
                    scope=rd.scope,
                )
            )
        return ir


class TypeScriptAdapter(JavaScriptAdapter):
    @property
    def language(self) -> str:
        return "typescript"

    @property
    def supported_extensions(self) -> list[str]:
        return [".ts", ".tsx", ".mts", ".cts"]

    def discover(self, workspace_root: Path) -> list[Path]:
        return sorted(list(workspace_root.rglob("*.ts")) + list(workspace_root.rglob("*.tsx")))

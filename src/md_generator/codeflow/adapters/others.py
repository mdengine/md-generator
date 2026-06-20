from __future__ import annotations

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
from md_generator.codeflow.enterprise_ir.graph import EnterpriseIR


class BaseFallbackAdapter(LanguageAdapter):
    @property
    def parser_backends(self) -> list[str]:
        return ["regex"]

    def discover(self, workspace_root: Path) -> list[Path]:
        res = []
        for ext in self.supported_extensions:
            res.extend(workspace_root.rglob(f"*{ext}"))
        return sorted(res)

    def extract_symbols(self, file_path: Path, backend: str) -> list[SymbolRecord]:
        return []

    def extract_imports(self, file_path: Path, backend: str) -> list[ImportRecord]:
        return []

    def extract_dependencies(self, file_path: Path, backend: str) -> list[RawDependency]:
        return []

    def extract_config_usage(self, file_path: Path, backend: str) -> list[ConfigUsage]:
        return []

    def extract_queries(self, file_path: Path, backend: str) -> list[RawQuery]:
        return []

    def extract_external_resources(self, file_path: Path, backend: str) -> list[RawResource]:
        return []

    def extract_events(self, file_path: Path, backend: str) -> list[RawEvent]:
        return []

    def build_ir(self, file_path: Path, backend: str, extracted_data: dict[str, Any]) -> EnterpriseIR:
        return EnterpriseIR()


class KotlinAdapter(BaseFallbackAdapter):
    @property
    def language(self) -> str:
        return "kotlin"

    @property
    def supported_extensions(self) -> list[str]:
        return [".kt", ".kts"]


class RustAdapter(BaseFallbackAdapter):
    @property
    def language(self) -> str:
        return "rust"

    @property
    def supported_extensions(self) -> list[str]:
        return [".rs"]


class CSharpAdapter(BaseFallbackAdapter):
    @property
    def language(self) -> str:
        return "csharp"

    @property
    def supported_extensions(self) -> list[str]:
        return [".cs"]


class SwiftAdapter(BaseFallbackAdapter):
    @property
    def language(self) -> str:
        return "swift"

    @property
    def supported_extensions(self) -> list[str]:
        return [".swift"]


class RubyAdapter(BaseFallbackAdapter):
    @property
    def language(self) -> str:
        return "ruby"

    @property
    def supported_extensions(self) -> list[str]:
        return [".rb"]


class LuaAdapter(BaseFallbackAdapter):
    @property
    def language(self) -> str:
        return "lua"

    @property
    def supported_extensions(self) -> list[str]:
        return [".lua"]


class CAdapter(BaseFallbackAdapter):
    @property
    def language(self) -> str:
        return "c"

    @property
    def supported_extensions(self) -> list[str]:
        return [".c", ".h"]


class CppAdapter(BaseFallbackAdapter):
    @property
    def language(self) -> str:
        return "cpp"

    @property
    def supported_extensions(self) -> list[str]:
        return [".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx"]

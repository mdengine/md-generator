from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from md_generator.codeflow.adapters import global_registry
from md_generator.codeflow.enterprise_ir.base import NodeMetadata, NodeType, PluginCategory
from md_generator.codeflow.enterprise_ir.config import ConfigEntity
from md_generator.codeflow.enterprise_ir.graph import EnterpriseIR
from md_generator.codeflow.plugins.base import BasePlugin, PluginMetadata
from md_generator.codeflow.repository.model import Repository


class ConfigurationPlugin(BasePlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="configuration",
            category=PluginCategory.PARSER,
            supported_languages=["python", "java", "javascript", "typescript", "go", "php"],
            supported_extensions=[".properties", ".yml", ".yaml", ".env", ".json", ".ini"],
            supports_incremental=True,
        )

    def discover(self, repository: Repository) -> list[Path]:
        res = []
        for ext in self.metadata.supported_extensions:
            res.extend(repository.path.rglob(f"*{ext}"))
        return sorted(res)

    def scan(self, file_path: Path) -> bool:
        return file_path.exists() and file_path.is_file()

    def extract(self, file_path: Path) -> Any:
        content = ""
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass
        return content

    def normalize(self, raw_payload: Any) -> Any:
        # Parse property lines e.g. key=value or key: value
        entries = []
        lines = raw_payload.splitlines()
        for idx, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("//"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                entries.append({"key": k.strip(), "value": v.strip(), "line": idx + 1})
            elif ":" in line:
                k, v = line.split(":", 1)
                entries.append({"key": k.strip(), "value": v.strip(), "line": idx + 1})
        return entries

    def validate(self, normalized_data: Any) -> bool:
        return isinstance(normalized_data, list)

    def post_process(self, normalized_data: Any) -> Any:
        # Resolve env expansion references like ${PORT:8080}
        for entry in normalized_data:
            val = entry["value"]
            match = re.match(r"^\$\{\s*([a-zA-Z0-9_]+)(?::(.*))?\s*\}$", val)
            if match:
                entry["env_var"] = match.group(1)
                entry["value"] = match.group(2) if match.group(2) else ""
        return normalized_data

    def build_ir(self, normalized_data: Any) -> EnterpriseIR:
        ir = EnterpriseIR()
        for entry in normalized_data:
            meta = NodeMetadata(
                id=f"config://{entry['key']}",
                kind=NodeType.CONFIG,
                language="mixed",
                repository="local",
                module=None,
                file="",
                line=entry["line"],
                column=0,
                confidence="MEDIUM",
                parser="configuration_plugin",
                backend="native",
            )
            ir.configs.append(
                ConfigEntity(
                    id=f"config://{entry['key']}",
                    metadata=meta,
                    key=entry["key"],
                    value=entry["value"],
                    type_name="string",
                    source="",
                    line=entry["line"],
                    env_var=entry.get("env_var"),
                )
            )
        return ir

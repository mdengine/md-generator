from __future__ import annotations

import re
import xml.etree.ElementTree as ET
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
from md_generator.codeflow.enterprise_ir.api import ApiEntity
from md_generator.codeflow.enterprise_ir.base import NodeMetadata, NodeType
from md_generator.codeflow.enterprise_ir.config import ConfigEntity
from md_generator.codeflow.enterprise_ir.database import TableEntity
from md_generator.codeflow.enterprise_ir.dependency import DependencyEntity
from md_generator.codeflow.enterprise_ir.event import EventEntity
from md_generator.codeflow.enterprise_ir.graph import EnterpriseIR, SemanticEntity
from md_generator.codeflow.enterprise_ir.query import QueryEntity
from md_generator.codeflow.enterprise_ir.resource import ResourceEntity
from md_generator.codeflow.enterprise_ir.runtime import RuntimeEntity


class JavaAdapter(LanguageAdapter):
    @property
    def language(self) -> str:
        return "java"

    @property
    def supported_extensions(self) -> list[str]:
        return [".java", ".xml"]

    @property
    def parser_backends(self) -> list[str]:
        return ["native", "treesitter", "regex"]

    def discover(self, workspace_root: Path) -> list[Path]:
        return sorted(list(workspace_root.rglob("*.java")) + list(workspace_root.rglob("pom.xml")))

    def extract_symbols(self, file_path: Path, backend: str) -> list[SymbolRecord]:
        records: list[SymbolRecord] = []
        if file_path.suffix.lower() != ".java":
            return records
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            # Class parsing regex
            class_matches = re.finditer(r"\b(?:class|interface|enum)\s+([a-zA-Z0-9_]+)", content)
            for m in class_matches:
                line_num = content.count("\n", 0, m.start()) + 1
                records.append(
                    SymbolRecord(
                        name=m.group(1),
                        kind="class",
                        line=line_num,
                        column=0,
                    )
                )
        except Exception:
            pass
        return records

    def extract_imports(self, file_path: Path, backend: str) -> list[ImportRecord]:
        imports: list[ImportRecord] = []
        if file_path.suffix.lower() != ".java":
            return imports
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            matches = re.finditer(r"\bimport\s+([a-zA-Z0-9_\.]+);", content)
            for m in matches:
                line_num = content.count("\n", 0, m.start()) + 1
                imports.append(
                    ImportRecord(
                        source_file=str(file_path),
                        imported_name=m.group(1).split(".")[-1],
                        import_path=m.group(1),
                        line=line_num,
                    )
                )
        except Exception:
            pass
        return imports

    def extract_dependencies(self, file_path: Path, backend: str) -> list[RawDependency]:
        deps: list[RawDependency] = []
        if file_path.name == "pom.xml":
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                # Remove namespaces if present
                ns = ""
                if root.tag.startswith("{"):
                    ns = root.tag.split("}")[0] + "}"
                
                # Fetch dependencies
                for dep in root.findall(f".//{ns}dependency"):
                    grp = dep.find(f"{ns}groupId")
                    art = dep.find(f"{ns}artifactId")
                    ver = dep.find(f"{ns}version")
                    scope = dep.find(f"{ns}scope")
                    
                    g_text = grp.text.strip() if grp is not None and grp.text else ""
                    a_text = art.text.strip() if art is not None and art.text else ""
                    v_text = ver.text.strip() if ver is not None and ver.text else "unknown"
                    s_text = scope.text.strip() if scope is not None and scope.text else "compile"
                    
                    if g_text and a_text:
                        deps.append(
                            RawDependency(
                                name=f"{g_text}:{a_text}",
                                version=v_text,
                                scope=s_text,
                                group=g_text,
                                artifact=a_text,
                            )
                        )
            except Exception:
                pass
        return deps

    def extract_config_usage(self, file_path: Path, backend: str) -> list[ConfigUsage]:
        usages: list[ConfigUsage] = []
        if file_path.suffix.lower() != ".java":
            return usages
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            # Scan for @Value("${config_key}")
            matches = re.finditer(r"@Value\(\s*[\'\"]\s*\$\{\s*([a-zA-Z0-9_\-\.]+)(?::.*?)?\s*\}\s*[\'\"]\s*\)", content)
            for m in matches:
                key = m.group(1)
                line_num = content.count("\n", 0, m.start()) + 1
                usages.append(
                    ConfigUsage(
                        key=key,
                        source_file=str(file_path),
                        line=line_num,
                        usage_type="Annotation",
                    )
                )
            
            # Scan for @ConfigurationProperties("config_prefix")
            prop_matches = re.finditer(r"@ConfigurationProperties\(\s*[\'\"]?([a-zA-Z0-9_\-\.]+)[\'\"]?\s*\)", content)
            for pm in prop_matches:
                prefix = pm.group(1)
                line_num = content.count("\n", 0, pm.start()) + 1
                usages.append(
                    ConfigUsage(
                        key=prefix,
                        source_file=str(file_path),
                        line=line_num,
                        usage_type="ConfigurationProperties",
                    )
                )
        except Exception:
            pass
        return usages

    def extract_queries(self, file_path: Path, backend: str) -> list[RawQuery]:
        queries: list[RawQuery] = []
        if file_path.suffix.lower() != ".java":
            return queries
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            # Search for typical embedded SELECT/INSERT/UPDATE queries inside java strings
            matches = re.finditer(r"[\'\"]\s*(SELECT|INSERT|UPDATE|DELETE|MERGE|CALL|EXEC)\s+.*?\s*[\'\"]", content, re.IGNORECASE)
            for m in matches:
                query_text = m.group(0).strip(" '\"")
                op = re.match(r"^\s*(SELECT|INSERT|UPDATE|DELETE|MERGE|CALL|EXEC)", query_text, re.IGNORECASE)
                op_name = op.group(1).upper() if op else "READ"
                line_num = content.count("\n", 0, m.start()) + 1
                
                tables = re.findall(
                    r"\b(?:FROM|JOIN|INTO|UPDATE)\s+([a-zA-Z0-9_\.]+)",
                    query_text,
                    re.IGNORECASE,
                )
                queries.append(
                    RawQuery(
                        query_text=query_text,
                        operation="READ" if op_name in ("SELECT", "CALL", "EXEC") else "WRITE",
                        database_type="SQL",
                        dialect="ANSI",
                        is_transactional=False,
                        is_read_only=(op_name == "SELECT"),
                        line=line_num,
                        tables=tables,
                    )
                )
        except Exception:
            pass
        return queries

    def extract_external_resources(self, file_path: Path, backend: str) -> list[RawResource]:
        resources: list[RawResource] = []
        if file_path.suffix.lower() != ".java":
            return resources
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            # Matches RestTemplate or WebClient usage or generic HTTP links
            matches = re.finditer(r"https?://[a-zA-Z0-9_\-\./]+", content)
            for m in matches:
                url = m.group(0)
                resources.append(
                    RawResource(
                        resource_type="REST",
                        uri=f"resource://https/{url.split('://')[1]}",
                        details={"url": url},
                    )
                )
        except Exception:
            pass
        return resources

    def extract_events(self, file_path: Path, backend: str) -> list[RawEvent]:
        events: list[RawEvent] = []
        if file_path.suffix.lower() != ".java":
            return events
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            # Scan for @KafkaListener(topics = "...")
            matches = re.finditer(r"@KafkaListener\(\s*(?:topics\s*=\s*)?[\'\"]([a-zA-Z0-9_\-\.]+)[\'\"]", content)
            for m in matches:
                topic = m.group(1)
                events.append(
                    RawEvent(
                        topic=topic,
                        queue=None,
                        broker="Kafka",
                        is_publisher=False,
                        is_consumer=True,
                    )
                )
        except Exception:
            pass
        return events

    def build_ir(self, file_path: Path, backend: str, extracted_data: dict[str, Any]) -> EnterpriseIR:
        ir = EnterpriseIR()
        repo_name = "local"
        
        # Add properties config usage keys
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
                parser="java_adapter",
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

        # Add Maven dependencies
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
                parser="java_adapter",
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
                    group=rd.group,
                    artifact=rd.artifact,
                )
            )

        # Add SQL queries
        for rq in extracted_data.get("queries", []):
            query_id = f"query://java-{hash(rq.query_text)}"
            meta = NodeMetadata(
                id=query_id,
                kind=NodeType.QUERY,
                language=self.language,
                repository=repo_name,
                module=None,
                file=str(file_path),
                line=rq.line,
                column=0,
                confidence="MEDIUM",
                parser="java_adapter",
                backend=backend,
            )
            ir.queries.append(
                QueryEntity(
                    id=query_id,
                    metadata=meta,
                    query_text=rq.query_text,
                    operation=rq.operation,
                    language_key=self.language,
                    database_type=rq.database_type,
                    dialect=rq.dialect,
                    is_read_only=rq.is_read_only,
                    is_transactional=rq.is_read_only,
                    source_file=str(file_path),
                    source_method="",
                    line_number=rq.line,
                    tables_referenced=rq.tables,
                )
            )
            for tbl in rq.tables:
                t_id = f"table://{tbl.upper()}"
                tbl_meta = NodeMetadata(
                    id=t_id,
                    kind=NodeType.TABLE,
                    language=self.language,
                    repository=repo_name,
                    module=None,
                    file=str(file_path),
                    line=rq.line,
                    column=0,
                    confidence="MEDIUM",
                    parser="java_adapter",
                    backend=backend,
                )
                ir.tables.append(
                    TableEntity(
                        id=t_id,
                        metadata=tbl_meta,
                        table_name=tbl,
                        database_type=rq.database_type,
                    )
                )

        return ir

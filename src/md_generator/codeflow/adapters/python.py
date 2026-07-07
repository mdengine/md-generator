from __future__ import annotations

import ast
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


class PythonAdapter(LanguageAdapter):
    @property
    def language(self) -> str:
        return "python"

    @property
    def supported_extensions(self) -> list[str]:
        return [".py"]

    @property
    def parser_backends(self) -> list[str]:
        return ["native", "treesitter", "regex"]

    def discover(self, workspace_root: Path) -> list[Path]:
        return sorted(list(workspace_root.rglob("*.py")))

    def extract_symbols(self, file_path: Path, backend: str) -> list[SymbolRecord]:
        records: list[SymbolRecord] = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(content, filename=str(file_path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    records.append(
                        SymbolRecord(
                            name=node.name,
                            kind="class",
                            line=node.lineno,
                            column=node.col_offset,
                        )
                    )
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    records.append(
                        SymbolRecord(
                            name=node.name,
                            kind="function",
                            line=node.lineno,
                            column=node.col_offset,
                        )
                    )
        except Exception:
            pass
        return records

    def extract_imports(self, file_path: Path, backend: str) -> list[ImportRecord]:
        imports: list[ImportRecord] = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(content, filename=str(file_path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append(
                            ImportRecord(
                                source_file=str(file_path),
                                imported_name=name.name,
                                import_path=name.name,
                                line=node.lineno,
                            )
                        )
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    for name in node.names:
                        imports.append(
                            ImportRecord(
                                source_file=str(file_path),
                                imported_name=name.name,
                                import_path=f"{mod}.{name.name}" if mod else name.name,
                                line=node.lineno,
                                is_relative=(node.level and node.level > 0),
                            )
                        )
        except Exception:
            pass
        return imports

    def extract_dependencies(self, file_path: Path, backend: str) -> list[RawDependency]:
        deps: list[RawDependency] = []
        # Find requirements.txt in the directory of the file or workspace root
        req_file = file_path.parent / "requirements.txt"
        if req_file.exists():
            try:
                for line in req_file.read_text(encoding="utf-8", errors="replace").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    # Match name==version or name>=version
                    match = re.match(r"^([a-zA-Z0-9_\-]+)(==|>=|<=|>|<)?(.*)$", line)
                    if match:
                        name, op, ver = match.groups()
                        deps.append(
                            RawDependency(
                                name=name.strip(),
                                version=ver.strip() if ver else "unknown",
                                scope="compile",
                            )
                        )
            except Exception:
                pass
        return deps

    def extract_config_usage(self, file_path: Path, backend: str) -> list[ConfigUsage]:
        usages: list[ConfigUsage] = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            # Look for environment variable usage e.g. os.getenv("PORT") or os.environ.get("DB_HOST")
            patterns = [
                r"os\.getenv\([\'\"]([a-zA-Z0-9_\-\.]+)[\'\"]",
                r"os\.environ\.get\([\'\"]([a-zA-Z0-9_\-\.]+)[\'\"]",
                r"os\.environ\[[\'\"]([a-zA-Z0-9_\-\.]+)[\'\"]",
            ]
            for pat in patterns:
                for match in re.finditer(pat, content):
                    key = match.group(1)
                    line_num = content.count("\n", 0, match.start()) + 1
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
        queries: list[RawQuery] = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            # Deterministic scan for embedded SQL statements matching SELECT, INSERT, UPDATE, DELETE
            sql_pattern = re.compile(
                r"([\'\"]{3}|[\'\"])\s*(SELECT|INSERT|UPDATE|DELETE|MERGE|CALL|EXEC)\s+.*?\1",
                re.DOTALL | re.IGNORECASE,
            )
            for match in sql_pattern.finditer(content):
                query_text = match.group(0).strip(" '\"")
                op = match.group(2).upper()
                line_num = content.count("\n", 0, match.start()) + 1
                
                # Simple table extraction e.g. FROM table_name or JOIN table_name
                tables = re.findall(
                    r"\b(?:FROM|JOIN|INTO|UPDATE)\s+([a-zA-Z0-9_\.]+)",
                    query_text,
                    re.IGNORECASE,
                )
                
                queries.append(
                    RawQuery(
                        query_text=query_text,
                        operation="READ" if op in ("SELECT", "CALL", "EXEC") else "WRITE",
                        database_type="SQL",
                        dialect="ANSI",
                        is_transactional=False,
                        is_read_only=(op == "SELECT"),
                        line=line_num,
                        tables=tables,
                    )
                )
            
            # Scan for MongoDB find/aggregate calls
            mongo_patterns = [
                (r"\.find\((.*?)\)", "READ"),
                (r"\.aggregate\((.*?)\)", "READ"),
                (r"\.insert_one\((.*?)\)", "WRITE"),
                (r"\.update_many\((.*?)\)", "WRITE"),
            ]
            for pat, op in mongo_patterns:
                for match in re.finditer(pat, content):
                    line_num = content.count("\n", 0, match.start()) + 1
                    queries.append(
                        RawQuery(
                            query_text=match.group(0),
                            operation=op,
                            database_type="MongoDB",
                            dialect="Mongo",
                            is_transactional=False,
                            is_read_only=(op == "READ"),
                            line=line_num,
                        )
                    )
        except Exception:
            pass
        return queries

    def extract_external_resources(self, file_path: Path, backend: str) -> list[RawResource]:
        resources: list[RawResource] = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            # Look for HTTP request urls e.g. requests.get("https://...") or client endpoints
            http_matches = re.finditer(r"https?://[a-zA-Z0-9_\-\./]+", content)
            for match in http_matches:
                url = match.group(0)
                resources.append(
                    RawResource(
                        resource_type="REST",
                        uri=f"resource://https/{url.split('://')[1]}",
                        details={"url": url},
                    )
                )
            # Look for boto3/s3 calls
            if "boto3.client('s3')" in content or "boto3.resource('s3')" in content:
                resources.append(
                    RawResource(
                        resource_type="S3",
                        uri="resource://s3/bucket",
                    )
                )
        except Exception:
            pass
        return resources

    def extract_events(self, file_path: Path, backend: str) -> list[RawEvent]:
        events: list[RawEvent] = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            # Heuristic checks for Kafka / RabbitMQ consumer/producer
            if "KafkaProducer" in content or "confluent_kafka" in content:
                events.append(
                    RawEvent(
                        topic="orders",
                        queue=None,
                        broker="Kafka",
                        is_publisher=True,
                        is_consumer=False,
                    )
                )
        except Exception:
            pass
        return events

    def build_ir(self, file_path: Path, backend: str, extracted_data: dict[str, Any]) -> EnterpriseIR:
        ir = EnterpriseIR()
        repo_name = "local"
        rel_file = file_path.name
        
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
                confidence="MEDIUM",
                parser="python_adapter",
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
            meta = NodeMetadata(
                id=f"dependency://{rd.name}",
                kind=NodeType.DEPENDENCY,
                language=self.language,
                repository=repo_name,
                module=None,
                file=str(file_path),
                line=0,
                column=0,
                confidence="HIGH",
                parser="python_adapter",
                backend=backend,
            )
            ir.dependencies.append(
                DependencyEntity(
                    id=f"dependency://{rd.name}",
                    metadata=meta,
                    name=rd.name,
                    version=rd.version,
                    language_key=self.language,
                    scope=rd.scope,
                )
            )

        # Populate queries
        for rq in extracted_data.get("queries", []):
            query_id = f"query://python-{hash(rq.query_text)}"
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
                parser="python_adapter",
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
                    is_transactional=rq.is_transactional,
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
                    parser="python_adapter",
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

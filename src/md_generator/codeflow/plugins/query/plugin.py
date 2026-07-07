from __future__ import annotations

from pathlib import Path
from typing import Any

from md_generator.codeflow.adapters import global_registry
from md_generator.codeflow.enterprise_ir.base import NodeMetadata, NodeType, PluginCategory
from md_generator.codeflow.enterprise_ir.database import TableEntity
from md_generator.codeflow.enterprise_ir.graph import EnterpriseIR
from md_generator.codeflow.enterprise_ir.query import QueryEntity, QueryDialect, QueryOperation
from md_generator.codeflow.plugins.base import BasePlugin, PluginMetadata
from md_generator.codeflow.repository.model import Repository


class QueryPlugin(BasePlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="query",
            category=PluginCategory.PARSER,
            supported_languages=["python", "java", "javascript", "typescript", "go", "php"],
            supported_extensions=[".py", ".java", ".js", ".ts", ".go", ".php", ".sql"],
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
        return adapter.extract_queries(file_path, backend)

    def normalize(self, raw_payload: Any) -> Any:
        return raw_payload

    def validate(self, normalized_data: Any) -> bool:
        return isinstance(normalized_data, list)

    def post_process(self, normalized_data: Any) -> Any:
        return normalized_data

    def build_ir(self, normalized_data: Any) -> EnterpriseIR:
        ir = EnterpriseIR()
        repo_name = "local"
        for idx, rq in enumerate(normalized_data):
            query_id = f"query://query-{idx}-{hash(rq.query_text)}"
            meta = NodeMetadata(
                id=query_id,
                kind=NodeType.QUERY,
                language="mixed",
                repository=repo_name,
                module=None,
                file=rq.query_text,
                line=rq.line,
                column=0,
                confidence="MEDIUM",
                parser="query_plugin",
                backend="native",
            )
            ir.queries.append(
                QueryEntity(
                    id=query_id,
                    metadata=meta,
                    query_text=rq.query_text,
                    operation=rq.operation,
                    language_key="mixed",
                    database_type=rq.database_type,
                    dialect=rq.dialect,
                    is_read_only=rq.is_read_only,
                    is_transactional=rq.is_transactional,
                    source_file="",
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
                    language="mixed",
                    repository=repo_name,
                    module=None,
                    file="",
                    line=rq.line,
                    column=0,
                    confidence="MEDIUM",
                    parser="query_plugin",
                    backend="native",
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

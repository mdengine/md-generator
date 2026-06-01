from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from md_generator.db.core.elasticsearch_output import elasticsearch_output_from_dict
from md_generator.db.core.elasticsearch_redaction import redaction_config_from_dict
from md_generator.db.core.models import ELASTICSEARCH_FEATURES, FEATURES
from md_generator.db.core.run_config import ErdConfig, RunConfig


class DatabaseSection(BaseModel):
    type: str = Field(
        ...,
        description="postgres | mysql | mssql | oracle | mongo | sqlite | access | elasticsearch",
    )
    uri: str
    schema: str | None = None
    database: str | None = None


class OutputSection(BaseModel):
    path: str = "./docs"
    split_files: bool = True
    write_combined_feature_markdown: bool = False
    readme_feature_merge: Literal["none", "inline", "toc"] = "none"
    write_manifest: bool = True
    markdown_cross_links: bool = True
    elasticsearch_mapping_mode: str | None = None
    elasticsearch_include_raw_json: bool | None = None
    elasticsearch_analyzer_format: str | None = None


class FeaturesSection(BaseModel):
    include: list[str] | None = None
    exclude: list[str] = Field(default_factory=list)


class ExecutionSection(BaseModel):
    workers: int = Field(default=4, ge=1, le=32)


class ErdSection(BaseModel):
    max_tables: int = Field(default=100, ge=1, le=100_000)
    scope: Literal["full", "per_schema", "per_table"] = Field(
        default="full",
        description="full | per_schema | per_table",
    )


class SecuritySection(BaseModel):
    redact_sensitive_values: bool = False
    redact_patterns: list[str] | None = None


class DbToMdRunBody(BaseModel):
    database: DatabaseSection
    output: OutputSection = Field(default_factory=OutputSection)
    features: FeaturesSection = Field(default_factory=FeaturesSection)
    execution: ExecutionSection = Field(default_factory=ExecutionSection)
    limits: dict[str, Any] = Field(default_factory=dict)
    erd: ErdSection = Field(default_factory=ErdSection)
    security: SecuritySection = Field(default_factory=SecuritySection)

    @model_validator(mode="after")
    def check_features(self) -> DbToMdRunBody:
        if self.features.include:
            bad = set(self.features.include) - FEATURES
            if bad:
                raise ValueError(f"Unknown features in include: {sorted(bad)}")
        bad_ex = set(self.features.exclude) - FEATURES
        if bad_ex:
            raise ValueError(f"Unknown features in exclude: {sorted(bad_ex)}")
        return self

    def to_run_config(self) -> RunConfig:
        db_t = self.database.type.lower().strip()
        if self.features.include:
            inc = frozenset(self.features.include)
        elif db_t in ("elasticsearch", "es"):
            inc = frozenset(ELASTICSEARCH_FEATURES)
        else:
            inc = frozenset(FEATURES)
        merge = self.output.readme_feature_merge
        write_combined = self.output.write_combined_feature_markdown
        if merge != "none" and self.output.split_files:
            write_combined = True
        es_out = elasticsearch_output_from_dict(
            self.output.model_dump(exclude_none=True),
        )
        security_cfg = redaction_config_from_dict(
            self.security.model_dump(exclude_none=True),
        )
        return RunConfig(
            db_type=self.database.type,
            uri=self.database.uri,
            schema=self.database.schema,
            database=self.database.database,
            output_path=Path(self.output.path),
            split_files=self.output.split_files,
            write_combined_feature_markdown=write_combined,
            readme_feature_merge=merge,
            write_manifest=self.output.write_manifest,
            markdown_cross_links=self.output.markdown_cross_links,
            include=inc,
            exclude=frozenset(self.features.exclude),
            workers=self.execution.workers,
            limits=dict(self.limits),
            erd=ErdConfig(max_tables=self.erd.max_tables, scope=self.erd.scope).normalized(),
            elasticsearch=es_out,
            security=security_cfg,
        )

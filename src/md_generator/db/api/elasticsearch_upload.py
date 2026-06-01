from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from md_generator.db.core.elasticsearch_output import (
    ElasticsearchOutputConfig,
    elasticsearch_output_from_dict,
)
from md_generator.db.core.models import ELASTICSEARCH_FEATURES, FEATURES
from md_generator.db.core.run_config import RunConfig


class ElasticsearchUploadOutputSection(BaseModel):
    path: str = "./docs"
    split_files: bool = True
    write_combined_feature_markdown: bool = False
    readme_feature_merge: Literal["none", "inline", "toc"] = "none"
    write_manifest: bool = True
    markdown_cross_links: bool = True
    elasticsearch_mapping_mode: str | None = None
    elasticsearch_include_raw_json: bool | None = None
    elasticsearch_analyzer_format: str | None = None


class ElasticsearchUploadFeaturesSection(BaseModel):
    include: list[str] | None = None
    exclude: list[str] = Field(default_factory=list)


class ElasticsearchUploadExecutionSection(BaseModel):
    workers: int = Field(default=4, ge=1, le=32)


class ElasticsearchUploadJsonBody(BaseModel):
    """Export options for Elasticsearch JSON/ZIP bundle upload (no live ``database`` block)."""

    output: ElasticsearchUploadOutputSection = Field(default_factory=ElasticsearchUploadOutputSection)
    features: ElasticsearchUploadFeaturesSection = Field(default_factory=ElasticsearchUploadFeaturesSection)
    execution: ElasticsearchUploadExecutionSection = Field(default_factory=ElasticsearchUploadExecutionSection)
    limits: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_features(self) -> ElasticsearchUploadJsonBody:
        if self.features.include:
            bad = set(self.features.include) - FEATURES
            if bad:
                raise ValueError(f"Unknown features in include: {sorted(bad)}")
        bad_ex = set(self.features.exclude) - FEATURES
        if bad_ex:
            raise ValueError(f"Unknown features in exclude: {sorted(bad_ex)}")
        return self

    def to_run_config(self, bundle_dir: Path) -> RunConfig:
        if self.features.include:
            inc = frozenset(self.features.include)
        else:
            inc = frozenset(ELASTICSEARCH_FEATURES)
        merge = self.output.readme_feature_merge
        write_combined = self.output.write_combined_feature_markdown
        if merge != "none" and self.output.split_files:
            write_combined = True
        es_out = elasticsearch_output_from_dict(self.output.model_dump(exclude_none=True))
        lim = dict(self.limits)
        lim["json_bundle_dir"] = str(bundle_dir.resolve())
        return RunConfig(
            db_type="elasticsearch",
            uri="json-bundle://local",
            schema=None,
            database=None,
            output_path=Path(self.output.path),
            split_files=self.output.split_files,
            write_combined_feature_markdown=write_combined,
            readme_feature_merge=merge,
            write_manifest=self.output.write_manifest,
            markdown_cross_links=self.output.markdown_cross_links,
            include=inc,
            exclude=frozenset(self.features.exclude),
            workers=self.execution.workers,
            limits=lim,
            elasticsearch=es_out,
        )


def parse_elasticsearch_upload_config_json(raw: str | None) -> ElasticsearchUploadJsonBody:
    if raw is None or not str(raw).strip():
        return ElasticsearchUploadJsonBody()
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("config must be a JSON object")
    return ElasticsearchUploadJsonBody.model_validate(data)

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator

from md_generator.sap.core.features import FEATURES
from md_generator.sap.core.run_config import SapRunConfig


class InputSection(BaseModel):
    paths: list[str] = Field(default_factory=list)


class OutputSection(BaseModel):
    path: str = "output/sap-md"
    split_files: bool = True
    write_manifest: bool = True
    markdown_cross_links: bool = True


class FeaturesSection(BaseModel):
    include: list[str] | None = None
    exclude: list[str] = Field(default_factory=list)


class SapToMdRunBody(BaseModel):
    input: InputSection = Field(default_factory=InputSection)
    output: OutputSection = Field(default_factory=OutputSection)
    features: FeaturesSection = Field(default_factory=FeaturesSection)
    chunking: dict[str, Any] = Field(default_factory=dict)
    graph: dict[str, Any] = Field(default_factory=dict)
    performance: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_features(self) -> SapToMdRunBody:
        if self.features.include:
            bad = set(self.features.include) - FEATURES
            if bad:
                raise ValueError(f"Unknown features: {sorted(bad)}")
        return self

    def to_run_config(self) -> SapRunConfig:
        from md_generator.sap.core.run_config import load_run_config

        return load_run_config(None, self.model_dump()).normalized()

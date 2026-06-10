from __future__ import annotations

from pathlib import Path
from typing import Protocol

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.graph.model import ArtifactGraph
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.parser.base import ParseContext, SapParseResult


class ArtifactParserPlugin(Protocol):
    name: str
    version: str

    def can_parse(self, path: Path) -> bool: ...
    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult | None: ...


class NormalizerPlugin(Protocol):
    name: str

    def normalize(self, obj: SapObject) -> tuple[CanonicalArtifact, ArtifactGraph]: ...


class GeneratorPlugin(Protocol):
    name: str
    version: str

    def generate(
        self,
        artifact: CanonicalArtifact,
        graph_store: object,
        output_dir: Path,
    ) -> list[Path]: ...


class RulePlugin(Protocol):
    rule_id: str

    def evaluate(self, artifact: CanonicalArtifact, graph_store: object) -> list[dict]: ...

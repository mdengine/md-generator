from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from md_generator.db.core.elasticsearch_redaction import (
    RedactionAudit,
    RedactionConfig,
    redact_elasticsearch_entity,
    redact_structure,
)
from md_generator.db.core.elasticsearch_export import export_elasticsearch_markdown
from md_generator.db.core.models import ElasticsearchPipelineInfo
from md_generator.db.core.run_config import RunConfig


def test_redact_structure_by_key_name() -> None:
    cfg = RedactionConfig(enabled=True)
    redacted, patterns = redact_structure(
        {"settings": {"password": "s3cr3t", "location": "/data"}},
        cfg,
    )
    assert redacted["settings"]["password"] == "[REDACTED]"
    assert redacted["settings"]["location"] == "/data"
    assert "password" in patterns


def test_redact_structure_disabled_by_default() -> None:
    obj = {"api_key": "abc"}
    redacted, patterns = redact_structure(obj, RedactionConfig(enabled=False))
    assert redacted == obj
    assert patterns == frozenset()


def test_redact_structure_url_credentials() -> None:
    cfg = RedactionConfig(enabled=True)
    redacted, patterns = redact_structure(
        {"endpoint": "https://user:pass@host:9200"},
        cfg,
    )
    assert "[REDACTED]" in redacted["endpoint"]
    assert "authorization" in patterns


def test_redact_pipeline_entity() -> None:
    pipe = ElasticsearchPipelineInfo(
        "ingest",
        {"processors": [{"set": {"field": "x", "value": "y"}}], "password": "hidden"},
    )
    cfg = RedactionConfig(enabled=True)
    redacted, patterns = redact_elasticsearch_entity(pipe, cfg)
    assert redacted.definition["password"] == "[REDACTED]"
    assert "password" in patterns


def test_redaction_audit_manifest() -> None:
    audit = RedactionAudit()
    audit.merge(frozenset({"password", "api_key"}))
    data = audit.to_manifest_dict()
    assert data["applied"] is True
    assert data["redacted_keys"] == ["api_key", "password"]


def test_export_pipeline_redaction_in_markdown_and_manifest(tmp_path: Path) -> None:
    adapter = MagicMock()
    adapter.db_type = "elasticsearch"
    adapter.get_ingest_pipelines.return_value = [
        ElasticsearchPipelineInfo("p", {"password": "secret-value"}),
    ]

    cfg = RunConfig(
        db_type="elasticsearch",
        uri="https://localhost:9200",
        output_path=tmp_path / "docs",
        include=frozenset({"elasticsearch_ingest_pipelines"}),
        write_manifest=True,
        security=RedactionConfig(enabled=True),
    )
    root = export_elasticsearch_markdown(cfg, adapter, cfg.effective_features(), cfg.output_path)
    md = (root / "elasticsearch" / "pipelines" / "p.md").read_text(encoding="utf-8")
    assert "[REDACTED]" in md
    assert "secret-value" not in md
    assert "## Export Warnings" in md
    assert "Redaction applied" in md

    manifest = (root / "export_manifest.json").read_text(encoding="utf-8")
    assert '"redaction"' in manifest
    assert '"password"' in manifest

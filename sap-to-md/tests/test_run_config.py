from __future__ import annotations

from md_generator.sap.core.run_config import load_run_config


def test_load_default_config():
    cfg = load_run_config(None, None).normalized()
    assert cfg.output_path.name == "sap-md"
    assert "entities" in cfg.effective_features()

from __future__ import annotations

import pytest

from md_generator.pipeline.config import PipelineConfig
from md_generator.security.policy import SecurityPolicy


def test_pipeline_config_default_fingerprint():
    config = PipelineConfig()
    fp1 = config.compute_fingerprint()
    assert isinstance(fp1, str)
    assert len(fp1) == 64  # SHA-256 hex string

    # Idempotency check
    fp2 = config.compute_fingerprint()
    assert fp1 == fp2


def test_pipeline_config_canonical_extra_metadata_key_order():
    config1 = PipelineConfig(extra_metadata={"z": 1, "a": 2, "m": 3})
    config2 = PipelineConfig(extra_metadata={"a": 2, "m": 3, "z": 1})
    assert config1.compute_fingerprint() == config2.compute_fingerprint()


def test_pipeline_config_canonical_extra_metadata_sets():
    config1 = PipelineConfig(extra_metadata={"tags": {"b", "a", "c"}})
    config2 = PipelineConfig(extra_metadata={"tags": {"c", "b", "a"}})
    assert config1.compute_fingerprint() == config2.compute_fingerprint()


def test_pipeline_config_tenant_boundary():
    config_default = PipelineConfig(tenant="default")
    config_tenant_a = PipelineConfig(tenant="tenant_a")
    assert config_default.compute_fingerprint() != config_tenant_a.compute_fingerprint()


def test_pipeline_config_altered_security_policy():
    policy1 = SecurityPolicy(enable_secret_redaction=True)
    policy2 = SecurityPolicy(enable_secret_redaction=False)
    config1 = PipelineConfig(security_policy=policy1)
    config2 = PipelineConfig(security_policy=policy2)
    assert config1.compute_fingerprint() != config2.compute_fingerprint()

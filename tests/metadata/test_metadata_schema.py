"""Contract & Tenant Boundary Tests for EnterpriseMetadata."""

import pytest
from md_generator.semantic.model.schema import InvalidSchemaError
from md_generator.metadata import EnterpriseMetadata


def test_enterprise_metadata_defaults():
    meta = EnterpriseMetadata()
    assert meta.tenant == "default"
    assert meta.system == "default"
    assert meta.environment == "production"
    assert meta.classification == "internal"


def test_enterprise_metadata_tenant_mandatory():
    # Empty tenant raises InvalidSchemaError
    with pytest.raises(InvalidSchemaError, match="EnterpriseMetadata.tenant must be a non-empty string isolation boundary"):
        EnterpriseMetadata(tenant="")

    # Whitespace tenant raises InvalidSchemaError
    with pytest.raises(InvalidSchemaError, match="EnterpriseMetadata.tenant must be a non-empty string isolation boundary"):
        EnterpriseMetadata(tenant="   ")


def test_enterprise_metadata_unknown_field_rejection():
    data = {
        "system": "SAP",
        "tenant": "tenant-100",
        "disallowed_field": "val",
    }
    with pytest.raises(InvalidSchemaError, match=r"Unknown fields for EnterpriseMetadata: \['disallowed_field'\]"):
        EnterpriseMetadata.from_dict(data)


def test_enterprise_metadata_serialization_roundtrip():
    meta = EnterpriseMetadata(
        repository="org/repo",
        source_uri="file:///main.py",
        system="ERP",
        domain="finance",
        tenant="tenant-abc",
    )
    d = meta.to_dict()
    reconstructed = EnterpriseMetadata.from_dict(d)
    assert reconstructed.tenant == "tenant-abc"
    assert reconstructed.to_json() == meta.to_json()

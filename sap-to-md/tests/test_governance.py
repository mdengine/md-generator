from __future__ import annotations

from md_generator.sap.analyzer.governance.classifier import classify_field, classify_objects
from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject


def test_classify_field_pii():
    assert classify_field("EMAIL_ADDR") == "PII"
    assert classify_field("WRBTR") == "FINANCIAL"


def test_classify_objects_ddic():
    obj = SapObject(
        kind=SapObjectKind.TABLE,
        name="KNA1",
        raw_metadata={
            "ddic": {
                "fields": [{"name": "EMAIL", "domain": "EMAIL"}],
            }
        },
    )
    out = classify_objects([obj])
    assert out and out[0]["classification"] == "PII"

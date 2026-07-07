from __future__ import annotations

from pathlib import Path

from md_generator.sap.parser.base import ParseContext
from md_generator.sap.parser.bw.adso import BwAdsoParser
from md_generator.sap.parser.bw.composite_provider import BwCompositeProviderParser
from md_generator.sap.parser.bw.dtp import BwDtpParser
from md_generator.sap.parser.bw.info_object import BwInfoObjectParser
from md_generator.sap.parser.bw.transformation import BwTransformationParser
from md_generator.sap.canonical.bw.adso import BwAdso
from md_generator.sap.canonical.bw.composite_provider import BwCompositeProvider
from md_generator.sap.canonical.bw.dtp import BwDtp
from md_generator.sap.canonical.bw.info_object import BwInfoObject
from md_generator.sap.canonical.bw.transformation import BwTransformation
from md_generator.sap.canonical.loader import load_canonical

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "bw" / "synthetic"


def test_bw_adso_golden():
    path = FIXTURES_DIR / "adso_sales.adso.json"
    result = BwAdsoParser().parse(path, ParseContext(root=FIXTURES_DIR))
    assert result and result.objects
    canonical_data = result.objects[0].raw_metadata["canonical"]
    artifact = load_canonical(canonical_data)
    assert isinstance(artifact, BwAdso)
    assert artifact.name == "ADSO_SALES"
    assert "CUSTOMER" in artifact.fields


def test_bw_cp_golden():
    path = FIXTURES_DIR / "cp_sales.compositeprovider.json"
    result = BwCompositeProviderParser().parse(path, ParseContext(root=FIXTURES_DIR))
    assert result and result.objects
    canonical_data = result.objects[0].raw_metadata["canonical"]
    artifact = load_canonical(canonical_data)
    assert isinstance(artifact, BwCompositeProvider)
    assert artifact.name == "CP_SALES"
    assert "ADSO_SALES" in artifact.members


def test_bw_transformation_golden():
    path = FIXTURES_DIR / "transformation_sales.transformation.json"
    result = BwTransformationParser().parse(path, ParseContext(root=FIXTURES_DIR))
    assert result and result.objects
    canonical_data = result.objects[0].raw_metadata["canonical"]
    artifact = load_canonical(canonical_data)
    assert isinstance(artifact, BwTransformation)
    assert artifact.name == "TR_SALES"
    assert len(artifact.rules) == 1
    assert artifact.rules[0]["target"] == "CUSTOMER"


def test_bw_info_object_golden():
    path = FIXTURES_DIR / "infoobject_sales.json"
    result = BwInfoObjectParser().parse(path, ParseContext(root=FIXTURES_DIR))
    assert result and result.objects
    canonical_data = result.objects[0].raw_metadata["canonical"]
    artifact = load_canonical(canonical_data)
    assert isinstance(artifact, BwInfoObject)
    assert artifact.name == "IO_SALES"
    assert "CUSTOMER" in artifact.characteristics


def test_bw_dtp_golden():
    path = FIXTURES_DIR / "dtp_sales.json"
    result = BwDtpParser().parse(path, ParseContext(root=FIXTURES_DIR))
    assert result and result.objects
    canonical_data = result.objects[0].raw_metadata["canonical"]
    artifact = load_canonical(canonical_data)
    assert isinstance(artifact, BwDtp)
    assert artifact.name == "DTP_SALES"
    assert artifact.source_name == "IO_SALES"
    assert artifact.target_name == "ADSO_SALES"

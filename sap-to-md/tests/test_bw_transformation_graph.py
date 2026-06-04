from pathlib import Path

import pytest

from md_generator.sap.parser.bw.dtp import BwDtpParser


FIXTURE = Path(__file__).parent / "fixtures" / "bw" / "synthetic" / "dtp_sales.json"


@pytest.mark.skipif(not FIXTURE.is_file(), reason="fixture missing")
def test_bw_dtp_parse():
    from md_generator.sap.parser.base import ParseContext

    result = BwDtpParser().parse(FIXTURE, ParseContext(root=FIXTURE.parent))
    assert result and result.objects
    canonical = result.objects[0].raw_metadata["canonical"]
    assert canonical["artifact_type"] == "bw.dtp"
    assert canonical["transformation_graph"]["execution_semantic"] == "bw_dtp"

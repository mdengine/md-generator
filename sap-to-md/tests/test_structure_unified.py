from __future__ import annotations

from pathlib import Path

from md_generator.sap.canonical.loader import canonical_from_object
from md_generator.sap.generators.registry import default_generator_registry
from md_generator.sap.graph.backends.memory import InMemoryGraphStore
from md_generator.sap.markdown.builders.ddic_adapters import structure_view_from_cds, structure_view_from_ddic
from md_generator.sap.markdown.builders.structure_sections import format_structure, format_structure_title
from md_generator.sap.normalizer.registry import default_normalizer_registry
from md_generator.sap.parser.base import ParseContext
from md_generator.sap.parser.cds.parser import CdsParserPlugin
from md_generator.sap.parser.ddic.adt_parser import AdtDdicParserPlugin

DDIC = Path(__file__).parent / "fixtures" / "ddic"
CDS = Path(__file__).parent / "fixtures" / "cds"


def test_format_structure_adt_vs_cds():
    adt_view = structure_view_from_ddic({
        "name": "BAL_S_CONT",
        "definition_source": "adt_xml",
        "components": [{"name": "MSG", "data_element": "SYCHAR100", "type_kind": ""}],
    })
    cds_view = structure_view_from_cds({
        "name": "BAL_S_MSG",
        "definition_source": "cds_ddl",
        "components": [{"name": "CONTEXT", "type_name": "BAL_S_CONT", "type_kind": "structure"}],
    })
    adt_md = format_structure_title(adt_view) + format_structure(adt_view)
    cds_md = format_structure_title(cds_view) + format_structure(cds_view)
    assert "adt_xml" in adt_md
    assert "cds_ddl" in cds_md
    assert "| Component |" in adt_md
    assert "BAL_S_CONT" in cds_md


def test_generator_writes_structures_path(tmp_path: Path):
    normalizer = default_normalizer_registry()
    store = InMemoryGraphStore(graph_id="test")
    artifacts = []
    ctx = ParseContext(root=DDIC)

    for fixture in (DDIC / "bal_s_cont.tabl.xml", CDS / "bal_s_msg.ddls"):
        if fixture.suffix == ".xml":
            obj = AdtDdicParserPlugin().parse(fixture, ctx).objects[0]
        else:
            obj = CdsParserPlugin().parse(fixture, ctx).objects[0]
        artifact, fragment = canonical_from_object(obj, normalizer)
        assert artifact is not None
        store.add_fragment(fragment)
        artifacts.append(artifact)

    gen = default_generator_registry()
    paths = gen.generate_all(artifacts, store, tmp_path)
    written = {p.as_posix() for p in paths}
    assert any("structures/bal_s_cont.md" in p for p in written)
    assert any("structures/bal_s_msg.md" in p for p in written)
    assert (tmp_path / "structures" / "bal_s_cont.md").is_file()
    assert (tmp_path / "structures" / "bal_s_msg.md").is_file()
    content = (tmp_path / "structures" / "bal_s_cont.md").read_text(encoding="utf-8")
    assert "Definition source" in content
    assert "MSG" in content


def test_structure_collision_note(tmp_path: Path):
    """Same name from ADT and CDS appends alternate definitions note."""
    normalizer = default_normalizer_registry()
    store = InMemoryGraphStore(graph_id="test")
    shared_meta = {
        "name": "ZSHARED",
        "description": "Shared",
        "definition_source": "adt_xml",
        "components": [{"name": "F1", "data_element": "CHAR10"}],
    }
    from md_generator.sap.models.entities.kinds import SapObjectKind
    from md_generator.sap.models.entities.sap_object import SapObject

    adt_obj = SapObject(
        kind=SapObjectKind.STRUCTURE,
        name="ZSHARED",
        raw_metadata={"structure": dict(shared_meta)},
    )
    cds_obj = SapObject(
        kind=SapObjectKind.CDS_STRUCTURE,
        name="ZSHARED",
        raw_metadata={
            "cds_structure": {
                "name": "ZSHARED",
                "definition_source": "cds_ddl",
                "components": [{"name": "F1", "type_name": "CHAR10", "type_kind": "type"}],
            }
        },
    )
    artifacts = []
    for obj in (adt_obj, cds_obj):
        artifact, fragment = canonical_from_object(obj, normalizer)
        assert artifact is not None
        store.add_fragment(fragment)
        artifacts.append(artifact)

    gen = default_generator_registry()
    gen.generate_all(artifacts, store, tmp_path)
    md = (tmp_path / "structures" / "zshared.md").read_text(encoding="utf-8")
    assert "Alternate definitions" in md

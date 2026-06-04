from pathlib import Path

from md_generator.sap.parser.registry import default_registry


def test_datasphere_view_parser_registered():
    reg = default_registry()
    path = Path(__file__).parent / "fixtures" / "datasphere" / "synthetic" / "ds_view_sales.json"
    plugin = reg.select(path)
    assert plugin is not None
    assert plugin.name == "datasphere.view"

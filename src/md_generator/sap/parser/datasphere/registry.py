from __future__ import annotations

from md_generator.sap.parser.base import SapParserPlugin


def default_datasphere_plugins() -> list[SapParserPlugin]:
    from md_generator.sap.parser.datasphere.analytical_model import DatasphereAnalyticalModelParser
    from md_generator.sap.parser.datasphere.data_flow import DatasphereDataFlowParser
    from md_generator.sap.parser.datasphere.view import DatasphereViewParser

    return [
        DatasphereAnalyticalModelParser(),
        DatasphereViewParser(),
        DatasphereDataFlowParser(),
    ]

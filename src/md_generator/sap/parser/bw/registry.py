from __future__ import annotations

from md_generator.sap.parser.base import SapParserPlugin


def default_bw_plugins() -> list[SapParserPlugin]:
    from md_generator.sap.parser.bw.adso import BwAdsoParser
    from md_generator.sap.parser.bw.composite_provider import BwCompositeProviderParser
    from md_generator.sap.parser.bw.dtp import BwDtpParser
    from md_generator.sap.parser.bw.info_object import BwInfoObjectParser
    from md_generator.sap.parser.bw.transformation import BwTransformationParser

    return [
        BwDtpParser(),
        BwInfoObjectParser(),
        BwAdsoParser(),
        BwCompositeProviderParser(),
        BwTransformationParser(),
    ]

from __future__ import annotations

from md_generator.sap.parser.base import SapParserPlugin


def default_external_plugins() -> list[SapParserPlugin]:
    from md_generator.sap.parser.external.dbt.manifest import DbtManifestParser
    from md_generator.sap.parser.external.informatica.mapping import InformaticaMappingParser
    from md_generator.sap.parser.external.kafka.schema import KafkaSchemaParser
    from md_generator.sap.parser.external.snowflake.ddl import SnowflakeDdlParser

    return [
        DbtManifestParser(),
        SnowflakeDdlParser(),
        KafkaSchemaParser(),
        InformaticaMappingParser(),
    ]

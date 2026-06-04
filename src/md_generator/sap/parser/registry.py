from __future__ import annotations

import importlib
from pathlib import Path

from md_generator.sap.parser.base import ParseContext, SapParseResult, SapParserPlugin


def _load_plugin(spec: str) -> SapParserPlugin | None:
    if ":" not in spec:
        return None
    mod_name, _, attr = spec.partition(":")
    mod = importlib.import_module(mod_name)
    obj = getattr(mod, attr, None)
    if obj is None:
        return None
    inst = obj() if callable(obj) else obj
    if isinstance(inst, SapParserPlugin):
        return inst
    return None


class ParserRegistry:
    def __init__(self) -> None:
        self._plugins: list[SapParserPlugin] = []

    def register(self, plugin: SapParserPlugin) -> None:
        self._plugins.append(plugin)

    def extend_from_specs(self, specs: list[str]) -> None:
        for spec in specs:
            p = _load_plugin(spec)
            if p:
                self._plugins.append(p)

    def select(self, path: Path) -> SapParserPlugin | None:
        for p in self._plugins:
            if p.can_parse(path):
                return p
        return None

    def parse_file(self, path: Path, ctx: ParseContext) -> SapParseResult | None:
        plugin = self.select(path)
        if not plugin:
            return None
        return plugin.parse(path, ctx)


def default_registry(cfg_parser: object | None = None) -> ParserRegistry:
    from md_generator.sap.parser.abap.parser import AbapParserPlugin
    from md_generator.sap.parser.bapi.parser import BapiParserPlugin
    from md_generator.sap.parser.cds.parser import CdsParserPlugin
    from md_generator.sap.parser.ddic.parser import DdicParserPlugin
    from md_generator.sap.parser.idoc.parser import IdocParserPlugin
    from md_generator.sap.parser.odata.parser import ODataParserPlugin
    from md_generator.sap.parser.transport.parser import TransportParserPlugin

    reg = ParserRegistry()
    flags = cfg_parser
    include = lambda attr, default=True: getattr(flags, attr, default) if flags else default

    if include("include_abap"):
        reg.register(AbapParserPlugin())
    if include("include_cds"):
        reg.register(CdsParserPlugin())
    if include("include_ddic"):
        reg.register(DdicParserPlugin())
    if include("include_odata"):
        reg.register(ODataParserPlugin())
    if include("include_bapi"):
        reg.register(BapiParserPlugin())
    if include("include_idoc"):
        reg.register(IdocParserPlugin())
    if include("include_transport"):
        reg.register(TransportParserPlugin())
    if include("include_hana"):
        from md_generator.sap.parser.hana.dispatch import HanaCalculationViewParserPlugin

        reg.register(HanaCalculationViewParserPlugin())
    if include("include_bw"):
        from md_generator.sap.parser.bw.registry import default_bw_plugins

        for p in default_bw_plugins():
            reg.register(p)
    if include("include_datasphere"):
        from md_generator.sap.parser.datasphere.registry import default_datasphere_plugins

        for p in default_datasphere_plugins():
            reg.register(p)
    if include("include_external"):
        from md_generator.sap.parser.external.registry import default_external_plugins

        for p in default_external_plugins():
            reg.register(p)

    if flags and getattr(flags, "plugins", None):
        reg.extend_from_specs(list(flags.plugins))
    return reg

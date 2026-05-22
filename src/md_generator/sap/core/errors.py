from __future__ import annotations


class SapToMdError(Exception):
    """Base error for SAP module."""


class ConfigurationError(SapToMdError):
    pass


class ParserError(SapToMdError):
    pass


class DiscoveryError(SapToMdError):
    pass

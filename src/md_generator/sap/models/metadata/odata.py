"""Re-export from shared OData core (md_generator.odata.models.domain)."""

from __future__ import annotations

from enum import Enum

from md_generator.odata.models.domain import *  # noqa: F403
from md_generator.odata.models.domain import (
    NavMultiplicity,
    ODataAction,
    ODataCapabilities,
    ODataComplexType,
    ODataEntitySet,
    ODataEntityType,
    ODataEnumType,
    ODataFormat,
    ODataFunction,
    ODataMetadataDocument,
    ODataNavigationProperty,
    ODataProperty,
    ODataVersion,
    make_stable_id,
)


class SapObjectCategory(str, Enum):
    PHYSICAL = "PHYSICAL"
    API = "API"
    METADATA = "METADATA"


__all__ = [
    "NavMultiplicity",
    "ODataAction",
    "ODataCapabilities",
    "ODataComplexType",
    "ODataEntitySet",
    "ODataEntityType",
    "ODataEnumType",
    "ODataFormat",
    "ODataFunction",
    "ODataMetadataDocument",
    "ODataNavigationProperty",
    "ODataProperty",
    "ODataVersion",
    "SapObjectCategory",
    "make_stable_id",
]

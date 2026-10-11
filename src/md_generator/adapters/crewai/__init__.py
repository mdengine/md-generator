"""Public facade for mdengine CrewAI tool adapters."""

from md_generator.adapters.crewai.exceptions import (
    CrewAIAdapterError,
    CrewAIDependencyError,
    CrewAIToolExecutionError,
    TenantBoundaryError,
)
from md_generator.adapters.crewai.schema import MDSearchInput
from md_generator.adapters.crewai.tools import MDSearchTool, detect_crewai_base_tool

__all__ = [
    "MDSearchTool",
    "detect_crewai_base_tool",
    "MDSearchInput",
    "CrewAIAdapterError",
    "CrewAIDependencyError",
    "CrewAIToolExecutionError",
    "TenantBoundaryError",
]

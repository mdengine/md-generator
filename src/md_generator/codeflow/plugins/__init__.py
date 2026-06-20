from __future__ import annotations

from md_generator.codeflow.plugins.base import BasePlugin, PluginMetadata
from md_generator.codeflow.plugins.config.plugin import ConfigurationPlugin
from md_generator.codeflow.plugins.dependency.plugin import DependencyPlugin
from md_generator.codeflow.plugins.external.plugin import ExternalPlugin
from md_generator.codeflow.plugins.query.plugin import QueryPlugin
from md_generator.codeflow.plugins.registry import ExtensionRegistry

# Create global extension registry and pre-register built-in plugins
global_plugin_registry = ExtensionRegistry()
global_plugin_registry.register(ConfigurationPlugin)
global_plugin_registry.register(DependencyPlugin)
global_plugin_registry.register(QueryPlugin)
global_plugin_registry.register(ExternalPlugin)

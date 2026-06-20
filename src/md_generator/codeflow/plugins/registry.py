from __future__ import annotations

import importlib
from typing import Type

from md_generator.codeflow.plugins.base import BasePlugin


class ExtensionRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, Type[BasePlugin]] = {}

    def register(self, plugin_class: Type[BasePlugin]) -> None:
        self._plugins[plugin_class.__name__] = plugin_class
        # Also register by lowercase metadata name if present
        try:
            meta = plugin_class.metadata
            if hasattr(meta, "name") and meta.name:
                self._plugins[meta.name] = plugin_class
        except (AttributeError, TypeError):
            pass

    def get_plugin(self, name: str) -> Type[BasePlugin] | None:
        return self._plugins.get(name)

    def list_plugins(self) -> list[Type[BasePlugin]]:
        # Deduplicated list of registered plugin classes
        seen = set()
        unique_plugins = []
        for p in self._plugins.values():
            if p not in seen:
                seen.add(p)
                unique_plugins.append(p)
        return unique_plugins

    def load_from_string(self, import_str: str) -> Type[BasePlugin]:
        """Dynamically imports a plugin class string (e.g. 'my_module.MyPlugin')."""
        if not import_str or "." not in import_str:
            raise ValueError(f"Invalid plugin import path: '{import_str}'")
        mod_name, class_name = import_str.rsplit(".", 1)
        mod = importlib.import_module(mod_name)
        plugin_class = getattr(mod, class_name)
        if not issubclass(plugin_class, BasePlugin):
            raise TypeError(f"Class '{import_str}' is not a subclass of BasePlugin")
        self.register(plugin_class)
        return plugin_class


def topological_sort_plugins(plugins: list[Type[BasePlugin]]) -> list[Type[BasePlugin]]:
    """Sorts plugins based on their dependency relationships ('depends_on')."""
    resolved: list[Type[BasePlugin]] = []
    seen: set[str] = set()

    # Build maps
    plugin_by_name = {}
    for p in plugins:
        try:
            name = p.metadata.name
            plugin_by_name[name] = p
        except Exception:
            plugin_by_name[p.__name__] = p

    def resolve(p_cls: Type[BasePlugin], path: list[str]) -> None:
        try:
            name = p_cls.metadata.name
        except Exception:
            name = p_cls.__name__

        if name in seen:
            return
        if name in path:
            # Cycle detected
            return

        path.append(name)
        try:
            deps = p_cls.metadata.depends_on
        except AttributeError:
            deps = []

        for dep in deps:
            if dep in plugin_by_name:
                resolve(plugin_by_name[dep], path)

        path.pop()
        seen.add(name)
        resolved.append(p_cls)

    for p in plugins:
        resolve(p, [])
    return resolved

"""Plugin registry for orchestration extensions and tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


PluginHandler = Callable[..., dict[str, Any]]


@dataclass
class PluginDefinition:
    """Metadata and callable for an orchestration plugin."""

    name: str
    description: str
    handler: PluginHandler
    version: str = "0.1.0"
    tags: list[str] = field(default_factory=list)

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the plugin handler."""
        return self.handler(**kwargs)


@dataclass
class PluginRegistry:
    """Runtime registry for orchestration plugins."""

    _plugins: dict[str, PluginDefinition] = field(default_factory=dict)

    def register(self, plugin: PluginDefinition) -> None:
        """Register a plugin definition."""
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin already registered: {plugin.name}")

        self._plugins[plugin.name] = plugin

    def get(self, name: str) -> PluginDefinition:
        """Retrieve a plugin by name."""
        if name not in self._plugins:
            raise KeyError(f"Unknown plugin: {name}")

        return self._plugins[name]

    def list_plugins(self) -> list[dict[str, Any]]:
        """Return serializable plugin metadata."""
        return [
            {
                "name": plugin.name,
                "description": plugin.description,
                "version": plugin.version,
                "tags": plugin.tags,
            }
            for plugin in self._plugins.values()
        ]

    def execute(self, name: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a registered plugin."""
        plugin = self.get(name)
        return plugin.execute(**kwargs)

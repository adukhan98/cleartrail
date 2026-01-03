"""Connector registry for managing available connectors."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.connectors.base import BaseConnector


class ConnectorRegistry:
    """Registry for managing connector instances."""

    def __init__(self) -> None:
        self._connectors: dict[str, type["BaseConnector"]] = {}

    def register(self, connector_type: str, connector_class: type["BaseConnector"]) -> None:
        """Register a connector class.

        Args:
            connector_type: Type identifier (e.g., "github")
            connector_class: The connector class to register
        """
        self._connectors[connector_type] = connector_class

    def get(self, connector_type: str) -> "BaseConnector | None":
        """Get a new connector instance by type.

        Args:
            connector_type: Type identifier

        Returns:
            New connector instance or None if not found
        """
        connector_class = self._connectors.get(connector_type)
        if connector_class:
            return connector_class()
        return None

    def list_types(self) -> list[str]:
        """List all registered connector types."""
        return list(self._connectors.keys())

    def is_registered(self, connector_type: str) -> bool:
        """Check if a connector type is registered."""
        return connector_type in self._connectors


# Global connector registry instance
connector_registry = ConnectorRegistry()


def register_connector(connector_type: str):
    """Decorator to register a connector class.

    Usage:
        @register_connector("github")
        class GitHubConnector(BaseConnector):
            ...
    """

    def decorator(cls: type["BaseConnector"]) -> type["BaseConnector"]:
        connector_registry.register(connector_type, cls)
        return cls

    return decorator

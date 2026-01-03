"""Abstract base connector interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, AsyncIterator


class ConnectionStatus(Enum):
    """Connection test result status."""

    CONNECTED = "connected"
    AUTH_ERROR = "auth_error"
    PERMISSION_ERROR = "permission_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class OAuthCredentials:
    """OAuth credentials for connector authentication."""

    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"
    expires_at: datetime | None = None
    scope: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectionTestResult:
    """Result of connection test."""

    status: ConnectionStatus
    message: str
    details: dict[str, Any] | None = None


@dataclass
class ResourceRef:
    """Reference to a resource in the source system."""

    id: str
    name: str
    type: str  # repo, project, folder, etc.
    url: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceFilter:
    """Filter for listing resources."""

    search: str | None = None
    resource_type: str | None = None
    limit: int = 100
    cursor: str | None = None


@dataclass
class DateRange:
    """Date range for artifact filtering."""

    start: date
    end: date


@dataclass
class RawArtifact:
    """Raw artifact from source system before normalization."""

    source_system: str
    source_object_id: str
    source_url: str
    source_created_at: datetime | None
    artifact_type: str
    title: str
    raw_content: dict[str, Any]
    captured_at: datetime

    # Period this artifact covers (for Type 2 audits)
    period_start: date | None = None
    period_end: date | None = None


class BaseConnector(ABC):
    """Abstract base class for all source system connectors.

    Each connector must implement this interface to enable
    plug-and-play integration with different source systems.
    """

    connector_type: str  # e.g., "github", "jira", "google_drive"

    def __init__(self, credentials: OAuthCredentials | None = None):
        """Initialize connector with optional credentials."""
        self._credentials = credentials

    @abstractmethod
    def get_oauth_url(self, state: str) -> str:
        """Generate OAuth authorization URL.

        Args:
            state: State parameter for CSRF protection (usually org_id)

        Returns:
            OAuth authorization URL to redirect user to
        """
        pass

    @abstractmethod
    async def exchange_code(self, code: str) -> OAuthCredentials:
        """Exchange authorization code for OAuth tokens.

        Args:
            code: Authorization code from OAuth callback

        Returns:
            OAuth credentials with access and refresh tokens
        """
        pass

    @abstractmethod
    async def refresh_access_token(self) -> OAuthCredentials:
        """Refresh expired access token using refresh token.

        Returns:
            New OAuth credentials

        Raises:
            AuthenticationError: If refresh token is invalid/expired
        """
        pass

    @abstractmethod
    async def test_connection(self) -> ConnectionTestResult:
        """Test connection health.

        Validates that current credentials work and have
        required permissions.

        Returns:
            Connection test result with status and details
        """
        pass

    @abstractmethod
    async def list_resources(
        self,
        filters: ResourceFilter | None = None,
    ) -> list[ResourceRef]:
        """List available resources in the source system.

        For GitHub: repositories
        For Jira: projects
        For Drive: folders

        Args:
            filters: Optional filters for the resource list

        Returns:
            List of resource references
        """
        pass

    @abstractmethod
    async def fetch_artifacts(
        self,
        resource_id: str,
        date_range: DateRange,
        artifact_types: list[str] | None = None,
    ) -> AsyncIterator[RawArtifact]:
        """Fetch artifacts from a specific resource.

        Args:
            resource_id: ID of the resource (repo, project, folder)
            date_range: Date range to fetch artifacts for
            artifact_types: Optional filter for artifact types

        Yields:
            Raw artifacts from the source system
        """
        pass

    @abstractmethod
    def get_artifact_url(self, artifact: RawArtifact) -> str:
        """Generate deep link URL to artifact in source system.

        Args:
            artifact: The artifact to generate URL for

        Returns:
            Direct URL to view artifact in source system
        """
        pass

    def set_credentials(self, credentials: OAuthCredentials) -> None:
        """Set credentials for authenticated requests."""
        self._credentials = credentials

    def _ensure_authenticated(self) -> None:
        """Raise error if not authenticated."""
        if self._credentials is None:
            raise AuthenticationError("Connector is not authenticated")


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


class PermissionError(Exception):
    """Raised when lacking required permissions."""

    pass


class RateLimitError(Exception):
    """Raised when rate limited by source system."""

    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after

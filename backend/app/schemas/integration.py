"""Integration and sync job schemas."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field, HttpUrl

from app.schemas.base import BaseSchema, TimestampSchema


class ConnectorType(str, Enum):
    """Supported connector types."""

    GITHUB = "github"
    JIRA = "jira"
    GOOGLE_DRIVE = "google_drive"


class IntegrationStatus(str, Enum):
    """Integration connection status."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PENDING = "pending"


class SyncJobStatus(str, Enum):
    """Sync job execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ============ Request Schemas ============


class IntegrationCreate(BaseSchema):
    """Schema for initiating integration setup."""

    connector_type: ConnectorType
    config: dict[str, Any] | None = Field(
        None,
        description="Optional configuration (e.g., selected repos, projects)",
    )


class OAuthCallback(BaseSchema):
    """OAuth callback data from provider."""

    code: str = Field(..., description="Authorization code from OAuth provider")
    state: str = Field(..., description="State parameter for CSRF protection")


class SyncTriggerRequest(BaseSchema):
    """Request to trigger a sync job."""

    date_range_start: datetime | None = Field(
        None,
        description="Start date for sync range (defaults to 90 days ago)",
    )
    date_range_end: datetime | None = Field(
        None,
        description="End date for sync range (defaults to now)",
    )
    resource_ids: list[str] | None = Field(
        None,
        description="Specific resources to sync (e.g., repo names, project keys)",
    )


# ============ Response Schemas ============


class AuthUrlResponse(BaseSchema):
    """OAuth authorization URL response."""

    auth_url: str
    state: str


class ConnectionTestResponse(BaseSchema):
    """Connection test result."""

    connected: bool
    message: str
    details: dict[str, Any] | None = None


class ResourceInfo(BaseSchema):
    """Information about a syncable resource."""

    id: str
    name: str
    description: str | None = None
    url: str | None = None


class ResourceListResponse(BaseSchema):
    """List of available resources to sync."""

    resources: list[ResourceInfo]
    total: int


class SyncJobResponse(BaseSchema):
    """Sync job status response."""

    id: UUID
    integration_id: UUID
    status: SyncJobStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    artifacts_found: int = 0
    artifacts_created: int = 0
    error_details: dict[str, Any] | None = None


class IntegrationResponse(TimestampSchema):
    """Integration response schema."""

    id: UUID
    org_id: UUID
    connector_type: ConnectorType
    status: IntegrationStatus
    last_sync_at: datetime | None = None
    config: dict[str, Any] | None = None

    # Computed fields for display
    display_name: str | None = None
    icon_url: str | None = None


class IntegrationWithSync(IntegrationResponse):
    """Integration with latest sync job info."""

    last_sync_job: SyncJobResponse | None = None


class IntegrationListResponse(BaseSchema):
    """List of integrations."""

    integrations: list[IntegrationResponse]
    total: int


class IntegrationDetailResponse(IntegrationResponse):
    """Detailed integration info including recent sync jobs."""

    recent_sync_jobs: list[SyncJobResponse] = []
    available_resources: list[ResourceInfo] = []

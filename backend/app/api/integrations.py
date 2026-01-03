"""Integration management endpoints."""

from enum import Enum
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import CurrentOrgId, CurrentUser, DbSession
from app.connectors.registry import connector_registry

router = APIRouter()


class IntegrationType(str, Enum):
    """Supported integration types."""

    GITHUB = "github"
    JIRA = "jira"
    GOOGLE_DRIVE = "google_drive"


class IntegrationStatus(str, Enum):
    """Integration connection status."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    SYNCING = "syncing"


class IntegrationResponse(BaseModel):
    """Integration response schema."""

    id: UUID
    type: IntegrationType
    status: IntegrationStatus
    last_sync_at: str | None
    config: dict | None

    class Config:
        from_attributes = True


class IntegrationListResponse(BaseModel):
    """List of integrations response."""

    integrations: list[IntegrationResponse]


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request."""

    code: str
    state: str


class ConnectionTestResponse(BaseModel):
    """Connection test result."""

    connected: bool
    message: str
    details: dict | None = None


@router.get("", response_model=IntegrationListResponse)
async def list_integrations(
    org_id: CurrentOrgId,
    db: DbSession,
) -> IntegrationListResponse:
    """List all integrations for the organization."""
    # TODO: Fetch from database
    return IntegrationListResponse(integrations=[])


@router.get("/{integration_type}/auth-url")
async def get_auth_url(
    integration_type: IntegrationType,
    org_id: CurrentOrgId,
) -> dict[str, str]:
    """Get OAuth authorization URL for integration."""
    connector = connector_registry.get(integration_type.value)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown integration type: {integration_type}",
        )
    auth_url = connector.get_oauth_url(str(org_id))
    return {"auth_url": auth_url}


@router.post("/{integration_type}/callback")
async def oauth_callback(
    integration_type: IntegrationType,
    request: OAuthCallbackRequest,
    org_id: CurrentOrgId,
    db: DbSession,
) -> IntegrationResponse:
    """Handle OAuth callback and store credentials."""
    connector = connector_registry.get(integration_type.value)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown integration type: {integration_type}",
        )

    # TODO: Exchange code for tokens and store
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="OAuth callback not yet implemented",
    )


@router.post("/{integration_id}/test", response_model=ConnectionTestResponse)
async def test_connection(
    integration_id: UUID,
    org_id: CurrentOrgId,
    db: DbSession,
) -> ConnectionTestResponse:
    """Test integration connection health."""
    # TODO: Fetch integration and test connection
    return ConnectionTestResponse(
        connected=False,
        message="Connection test not yet implemented",
    )


@router.post("/{integration_id}/sync")
async def trigger_sync(
    integration_id: UUID,
    org_id: CurrentOrgId,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    """Trigger manual sync for integration."""
    # TODO: Queue sync job via Celery
    return {"message": "Sync job queued", "job_id": "placeholder"}


@router.delete("/{integration_id}")
async def disconnect_integration(
    integration_id: UUID,
    org_id: CurrentOrgId,
    db: DbSession,
) -> dict[str, str]:
    """Disconnect and remove integration."""
    # TODO: Revoke tokens and delete integration
    return {"message": "Integration disconnected"}

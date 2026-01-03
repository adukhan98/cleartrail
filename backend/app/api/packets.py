"""Evidence packet endpoints."""

from datetime import date
from enum import Enum
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import CurrentOrgId, CurrentUser, DbSession

router = APIRouter()


class PacketStatus(str, Enum):
    """Evidence packet status."""

    DRAFT = "draft"
    NARRATIVE_PENDING = "narrative_pending"
    NARRATIVE_READY = "narrative_ready"
    APPROVED = "approved"
    EXPORTED = "exported"


class PacketItemResponse(BaseModel):
    """Evidence packet item."""

    artifact_id: UUID
    artifact_type: str
    title: str
    source_url: str
    display_order: int


class PacketResponse(BaseModel):
    """Evidence packet response."""

    id: UUID
    control_id: str
    control_title: str
    title: str
    period_start: date
    period_end: date
    status: PacketStatus
    items: list[PacketItemResponse]
    ai_narrative: str | None
    narrative_approved_by: str | None
    narrative_approved_at: str | None
    created_at: str
    exported_at: str | None

    class Config:
        from_attributes = True


class CreatePacketRequest(BaseModel):
    """Create packet request."""

    control_id: str
    title: str
    period_start: date
    period_end: date
    artifact_ids: list[UUID]


class PacketListResponse(BaseModel):
    """List of packets response."""

    packets: list[PacketResponse]
    total: int


@router.get("", response_model=PacketListResponse)
async def list_packets(
    org_id: CurrentOrgId,
    db: DbSession,
    control_id: str | None = None,
    status: PacketStatus | None = None,
) -> PacketListResponse:
    """List evidence packets."""
    return PacketListResponse(packets=[], total=0)


@router.post("", response_model=PacketResponse)
async def create_packet(
    request: CreatePacketRequest,
    org_id: CurrentOrgId,
    current_user: CurrentUser,
    db: DbSession,
) -> PacketResponse:
    """Create a new evidence packet."""
    # TODO: Implement packet creation
    raise NotImplementedError("Packet creation not yet implemented")


@router.get("/{packet_id}", response_model=PacketResponse)
async def get_packet(
    packet_id: UUID,
    org_id: CurrentOrgId,
    db: DbSession,
) -> PacketResponse:
    """Get packet details."""
    raise NotImplementedError("Packet fetch not yet implemented")


@router.post("/{packet_id}/add-artifact")
async def add_artifact_to_packet(
    packet_id: UUID,
    artifact_id: UUID,
    org_id: CurrentOrgId,
    db: DbSession,
) -> dict[str, str]:
    """Add artifact to packet."""
    return {"message": "Artifact added to packet"}


@router.delete("/{packet_id}/artifacts/{artifact_id}")
async def remove_artifact_from_packet(
    packet_id: UUID,
    artifact_id: UUID,
    org_id: CurrentOrgId,
    db: DbSession,
) -> dict[str, str]:
    """Remove artifact from packet."""
    return {"message": "Artifact removed from packet"}


@router.post("/{packet_id}/generate-narrative")
async def generate_narrative(
    packet_id: UUID,
    org_id: CurrentOrgId,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    """Trigger AI narrative generation for packet."""
    # TODO: Queue Celery task for narrative generation
    return {"message": "Narrative generation started", "job_id": "placeholder"}


@router.post("/{packet_id}/approve-narrative")
async def approve_narrative(
    packet_id: UUID,
    org_id: CurrentOrgId,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    """Approve AI-generated narrative."""
    return {"message": "Narrative approved"}


@router.post("/{packet_id}/reject-narrative")
async def reject_narrative(
    packet_id: UUID,
    feedback: str,
    org_id: CurrentOrgId,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    """Reject narrative with feedback for regeneration."""
    return {"message": "Narrative rejected, regeneration queued"}

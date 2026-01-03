"""Evidence packet schemas."""

from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, PaginatedResponse, TimestampSchema


class PacketStatus(str, Enum):
    """Evidence packet status."""

    DRAFT = "draft"
    NARRATIVE_PENDING = "narrative_pending"
    NARRATIVE_READY = "narrative_ready"
    APPROVED = "approved"
    EXPORTED = "exported"


# ============ Request Schemas ============


class PacketCreate(BaseSchema):
    """Request to create an evidence packet."""

    control_id: str = Field(..., description="Control this packet is for (e.g., CC7.1)")
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    period_start: date
    period_end: date
    artifact_ids: list[UUID] = Field(
        ...,
        min_length=1,
        description="Artifacts to include in this packet",
    )


class PacketUpdate(BaseSchema):
    """Request to update a packet."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)


class PacketAddItems(BaseSchema):
    """Request to add artifacts to a packet."""

    artifact_ids: list[UUID]


class PacketRemoveItems(BaseSchema):
    """Request to remove artifacts from a packet."""

    artifact_ids: list[UUID]


class PacketReorderItems(BaseSchema):
    """Request to reorder packet items."""

    item_order: list[UUID] = Field(
        ...,
        description="List of artifact IDs in desired order",
    )


class NarrativeGenerateRequest(BaseSchema):
    """Request to generate AI narrative."""

    regenerate: bool = Field(
        False,
        description="Whether to regenerate if narrative already exists",
    )
    feedback: str | None = Field(
        None,
        max_length=1000,
        description="Feedback for regeneration (if regenerate=True)",
    )


class NarrativeApproveRequest(BaseSchema):
    """Request to approve the narrative."""

    notes: str | None = Field(None, max_length=500)


# ============ Response Schemas ============


class PacketItemResponse(BaseSchema):
    """Packet item (artifact reference) response."""

    id: UUID
    artifact_id: UUID
    display_order: int

    # Denormalized artifact info for display
    artifact_title: str
    artifact_type: str
    source_system: str
    source_url: str
    approval_status: str


class NarrativeResponse(BaseSchema):
    """AI narrative response."""

    content: str
    generated_at: datetime
    approved: bool = False
    approved_by: str | None = None
    approved_at: datetime | None = None


class PacketResponse(TimestampSchema):
    """Basic packet response for lists."""

    id: UUID
    org_id: UUID
    control_id: str
    title: str
    description: str | None = None
    period_start: date
    period_end: date
    status: PacketStatus
    item_count: int = 0
    has_narrative: bool = False
    exported_at: datetime | None = None


class PacketDetailResponse(PacketResponse):
    """Detailed packet with items and narrative."""

    items: list[PacketItemResponse] = []
    narrative: NarrativeResponse | None = None
    drive_folder_url: str | None = None

    # Audit info
    created_by: str | None = None
    narrative_approved_by: str | None = None
    narrative_approved_at: datetime | None = None


class PacketListResponse(PaginatedResponse[PacketResponse]):
    """Paginated list of packets."""

    pass


class PacketStatusUpdate(BaseSchema):
    """Response after status change."""

    packet_id: UUID
    old_status: PacketStatus
    new_status: PacketStatus
    message: str

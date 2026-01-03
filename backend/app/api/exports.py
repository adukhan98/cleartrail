"""Export endpoints for generating audit-ready packages."""

from enum import Enum
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import CurrentOrgId, CurrentUser, DbSession

router = APIRouter()


class ExportFormat(str, Enum):
    """Export format options."""

    GOOGLE_DRIVE = "google_drive"
    ZIP = "zip"


class ExportStatus(str, Enum):
    """Export job status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportJobResponse(BaseModel):
    """Export job response."""

    id: UUID
    packet_id: UUID
    format: ExportFormat
    status: ExportStatus
    drive_folder_url: str | None
    download_url: str | None
    error_message: str | None
    started_at: str
    completed_at: str | None


class ExportRequest(BaseModel):
    """Export request."""

    format: ExportFormat = ExportFormat.GOOGLE_DRIVE
    include_raw_artifacts: bool = True
    include_manifest: bool = True


class ManifestItem(BaseModel):
    """Evidence manifest item."""

    artifact_id: str
    artifact_type: str
    title: str
    source_system: str
    source_url: str
    captured_at: str
    content_hash: str
    control_mapping: str
    approval_status: str
    approved_by: str | None
    approved_at: str | None


class ManifestResponse(BaseModel):
    """Evidence manifest for auditor."""

    packet_id: str
    control_id: str
    control_title: str
    audit_period_start: str
    audit_period_end: str
    generated_at: str
    generated_by: str
    narrative: str | None
    narrative_approved_by: str | None
    narrative_approved_at: str | None
    items: list[ManifestItem]
    total_items: int
    approved_items: int


@router.post("/packets/{packet_id}/export", response_model=ExportJobResponse)
async def export_packet(
    packet_id: UUID,
    request: ExportRequest,
    org_id: CurrentOrgId,
    current_user: CurrentUser,
    db: DbSession,
) -> ExportJobResponse:
    """Export evidence packet to Drive folder or ZIP."""
    # TODO: Queue export job via Celery
    raise NotImplementedError("Export not yet implemented")


@router.get("/jobs/{job_id}", response_model=ExportJobResponse)
async def get_export_job(
    job_id: UUID,
    org_id: CurrentOrgId,
    db: DbSession,
) -> ExportJobResponse:
    """Get export job status."""
    raise NotImplementedError("Export job fetch not yet implemented")


@router.get("/packets/{packet_id}/manifest", response_model=ManifestResponse)
async def get_manifest(
    packet_id: UUID,
    org_id: CurrentOrgId,
    db: DbSession,
) -> ManifestResponse:
    """Get evidence manifest for packet."""
    # TODO: Generate manifest from packet
    raise NotImplementedError("Manifest generation not yet implemented")

"""Export schemas for audit-ready packages."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema


class ExportFormat(str, Enum):
    """Supported export formats."""

    GOOGLE_DRIVE = "google_drive"
    ZIP = "zip"


class ExportStatus(str, Enum):
    """Export job status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# ============ Request Schemas ============


class ExportRequest(BaseSchema):
    """Request to export an evidence packet."""

    format: ExportFormat = ExportFormat.GOOGLE_DRIVE
    include_raw_content: bool = Field(
        False,
        description="Include raw JSON content in export",
    )
    folder_id: str | None = Field(
        None,
        description="Google Drive folder ID to export to (uses default if not specified)",
    )


class BulkExportRequest(BaseSchema):
    """Request to export multiple packets."""

    packet_ids: list[UUID]
    format: ExportFormat = ExportFormat.GOOGLE_DRIVE
    create_parent_folder: bool = Field(
        True,
        description="Create a parent folder containing all packet exports",
    )


# ============ Response Schemas ============


class ExportJobResponse(BaseSchema):
    """Export job status response."""

    id: UUID
    packet_id: UUID
    format: ExportFormat
    status: ExportStatus
    started_at: datetime
    completed_at: datetime | None = None

    # Results
    drive_folder_url: str | None = None
    download_url: str | None = None
    error_message: str | None = None


class ManifestItemResponse(BaseSchema):
    """Single item in the evidence manifest."""

    artifact_id: str
    display_order: int
    title: str
    artifact_type: str
    source_system: str
    source_object_id: str
    source_url: str
    source_created_at: str | None = None
    captured_at: str
    content_hash: str
    approval_status: str
    approved_by: str | None = None
    approved_at: str | None = None
    signature_hash: str | None = None
    control_mappings: list[dict[str, Any]] = []


class ManifestNarrativeResponse(BaseSchema):
    """Narrative section of manifest."""

    content: str
    generated_at: str | None = None
    approved_by: str | None = None
    approved_at: str | None = None


class ManifestSummaryResponse(BaseSchema):
    """Summary statistics in manifest."""

    total_items: int
    approved_items: int
    pending_items: int
    by_source: dict[str, int]
    by_type: dict[str, int]


class ManifestResponse(BaseSchema):
    """Complete evidence manifest for auditor."""

    manifest_version: str = "1.0"
    packet_id: str
    control_id: str
    title: str
    audit_period_start: str
    audit_period_end: str
    generated_at: str
    generated_by: str
    narrative: ManifestNarrativeResponse
    evidence_items: list[ManifestItemResponse]
    summary: ManifestSummaryResponse


class ExportPreviewResponse(BaseSchema):
    """Preview of what will be exported."""

    packet_id: UUID
    control_id: str
    title: str
    folder_structure: dict[str, str] = Field(
        ...,
        description="Mapping of file paths to descriptions",
    )
    estimated_size_bytes: int | None = None
    item_count: int

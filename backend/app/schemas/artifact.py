"""Evidence artifact schemas."""

from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field, HttpUrl

from app.schemas.base import BaseSchema, PaginatedResponse, TimestampSchema


class ArtifactType(str, Enum):
    """Types of evidence artifacts."""

    PULL_REQUEST = "pull_request"
    COMMIT = "commit"
    CODE_REVIEW = "code_review"
    JIRA_ISSUE = "jira_issue"
    DOCUMENT = "document"
    POLICY = "policy"
    MEETING_NOTES = "meeting_notes"
    OTHER = "other"


class ApprovalStatus(str, Enum):
    """Artifact approval status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MappingSource(str, Enum):
    """How the control mapping was created."""

    AUTO = "auto"
    MANUAL = "manual"
    AI = "ai"


# ============ Response Schemas ============


class ControlMappingResponse(BaseSchema):
    """Control mapping response."""

    id: UUID
    artifact_id: UUID
    control_id: str
    mapping_source: MappingSource
    mapping_rationale: str | None = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    created_at: datetime


class ApprovalRecordResponse(BaseSchema):
    """Approval record response."""

    id: UUID
    artifact_id: UUID
    user_id: UUID
    user_name: str | None = None
    approved: bool
    approved_at: datetime
    notes: str | None = None
    signature_hash: str


class ArtifactResponse(TimestampSchema):
    """Basic artifact response for lists."""

    id: UUID
    source_system: str
    source_object_id: str
    source_url: str
    artifact_type: ArtifactType
    title: str
    captured_at: datetime
    period_start: date | None = None
    period_end: date | None = None
    approval_status: ApprovalStatus
    control_ids: list[str] = Field(default_factory=list, description="Mapped control IDs")


class ArtifactDetailResponse(ArtifactResponse):
    """Detailed artifact response with full content."""

    org_id: UUID
    sync_job_id: UUID | None = None
    source_created_at: datetime | None = None
    content_hash: str
    raw_content: dict[str, Any]
    normalized_content: dict[str, Any]
    control_mappings: list[ControlMappingResponse] = []
    approval_history: list[ApprovalRecordResponse] = []


class ArtifactListResponse(PaginatedResponse[ArtifactResponse]):
    """Paginated list of artifacts."""

    pass


# ============ Request Schemas ============


class ArtifactApprovalRequest(BaseSchema):
    """Request to approve or reject an artifact."""

    approved: bool
    notes: str | None = Field(None, max_length=1000)


class ArtifactApprovalResponse(BaseSchema):
    """Approval action response."""

    artifact_id: UUID
    approval_id: UUID
    approved: bool
    approved_at: datetime
    approved_by: str
    signature_hash: str


class ControlMappingCreate(BaseSchema):
    """Request to manually map artifact to control."""

    control_id: str
    rationale: str = Field(..., min_length=10, max_length=500)


class ArtifactFilterParams(BaseSchema):
    """Filter parameters for artifact list."""

    source_system: str | None = None
    artifact_type: ArtifactType | None = None
    approval_status: ApprovalStatus | None = None
    control_id: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    search: str | None = Field(None, description="Search in title")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


# ============ Coverage Schemas ============


class MonthCoverage(BaseSchema):
    """Coverage for a single month."""

    month: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="YYYY-MM format")
    has_evidence: bool
    artifact_count: int = 0


class CoverageReportResponse(BaseSchema):
    """Period coverage report for a control."""

    control_id: str
    control_name: str
    period_start: date
    period_end: date
    months: list[MonthCoverage]
    coverage_percentage: float = Field(..., ge=0.0, le=100.0)
    artifact_count: int
    approved_count: int

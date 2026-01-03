"""Evidence artifact endpoints."""

from datetime import date
from enum import Enum
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.api.deps import CurrentOrgId, CurrentUser, DbSession

router = APIRouter()


class ArtifactType(str, Enum):
    """Evidence artifact types."""

    PULL_REQUEST = "pull_request"
    COMMIT = "commit"
    CODE_REVIEW = "code_review"
    JIRA_ISSUE = "jira_issue"
    DOCUMENT = "document"
    MEETING_NOTES = "meeting_notes"
    POLICY = "policy"


class ArtifactStatus(str, Enum):
    """Artifact approval status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ArtifactResponse(BaseModel):
    """Evidence artifact response."""

    id: UUID
    source_system: str
    source_object_id: str
    source_url: str
    artifact_type: ArtifactType
    title: str
    captured_at: str
    period_start: date | None
    period_end: date | None
    status: ArtifactStatus
    control_mappings: list[str]
    approved_by: str | None
    approved_at: str | None

    class Config:
        from_attributes = True


class ArtifactListResponse(BaseModel):
    """Paginated artifact list."""

    artifacts: list[ArtifactResponse]
    total: int
    page: int
    page_size: int


class ArtifactDetailResponse(ArtifactResponse):
    """Detailed artifact with full content."""

    raw_content: dict
    normalized_content: dict
    content_hash: str
    mapping_rationale: str | None


class ApprovalRequest(BaseModel):
    """Artifact approval request."""

    approved: bool
    notes: str | None = None


class CoverageResponse(BaseModel):
    """Period coverage report."""

    control_id: str
    control_name: str
    period_start: date
    period_end: date
    months_covered: list[str]
    months_missing: list[str]
    coverage_percentage: float
    artifact_count: int


@router.get("", response_model=ArtifactListResponse)
async def list_artifacts(
    org_id: CurrentOrgId,
    db: DbSession,
    source_system: str | None = None,
    artifact_type: ArtifactType | None = None,
    control_id: str | None = None,
    status: ArtifactStatus | None = None,
    period_start: date | None = None,
    period_end: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ArtifactListResponse:
    """List evidence artifacts with filtering."""
    # TODO: Implement database query with filters
    return ArtifactListResponse(
        artifacts=[],
        total=0,
        page=page,
        page_size=page_size,
    )


@router.get("/coverage", response_model=list[CoverageResponse])
async def get_coverage_report(
    org_id: CurrentOrgId,
    db: DbSession,
    period_start: date = Query(...),
    period_end: date = Query(...),
    control_pack: str | None = None,
) -> list[CoverageResponse]:
    """Get period coverage report for gap detection."""
    # TODO: Calculate coverage across controls
    return []


@router.get("/{artifact_id}", response_model=ArtifactDetailResponse)
async def get_artifact(
    artifact_id: UUID,
    org_id: CurrentOrgId,
    db: DbSession,
) -> ArtifactDetailResponse:
    """Get artifact details including full content."""
    # TODO: Fetch artifact from database
    raise NotImplementedError("Artifact fetch not yet implemented")


@router.post("/{artifact_id}/approve")
async def approve_artifact(
    artifact_id: UUID,
    request: ApprovalRequest,
    org_id: CurrentOrgId,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    """Approve or reject an artifact."""
    # TODO: Record approval in database
    return {"message": f"Artifact {'approved' if request.approved else 'rejected'}"}


@router.post("/{artifact_id}/map")
async def map_to_control(
    artifact_id: UUID,
    control_id: str,
    rationale: str,
    org_id: CurrentOrgId,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    """Manually map artifact to a control."""
    # TODO: Create control mapping
    return {"message": f"Artifact mapped to control {control_id}"}

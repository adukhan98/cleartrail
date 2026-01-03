"""Control management endpoints."""

from enum import Enum
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.api.deps import CurrentOrgId, DbSession

router = APIRouter()


class Framework(str, Enum):
    """Compliance frameworks."""

    SOC2 = "soc2"
    ISO27001 = "iso27001"


class ControlResponse(BaseModel):
    """Control response schema."""

    id: str
    framework: Framework
    control_id: str
    title: str
    description: str
    required_evidence_types: list[str]
    artifact_count: int
    approved_count: int
    coverage_status: str  # complete, partial, missing

    class Config:
        from_attributes = True


class ControlListResponse(BaseModel):
    """List of controls response."""

    controls: list[ControlResponse]
    total: int


class GapResponse(BaseModel):
    """Control gap detection response."""

    control_id: str
    control_title: str
    gap_type: str  # missing_artifact, missing_approval, incomplete_period
    description: str
    severity: str  # high, medium, low
    recommended_action: str


@router.get("", response_model=ControlListResponse)
async def list_controls(
    org_id: CurrentOrgId,
    db: DbSession,
    framework: Framework | None = None,
    control_pack: str | None = None,
) -> ControlListResponse:
    """List available controls."""
    # Return Change Management control pack for MVP
    change_mgmt_controls = [
        ControlResponse(
            id="cc7.1",
            framework=Framework.SOC2,
            control_id="CC7.1",
            title="Change Management",
            description="The entity uses a defined change management process for all changes to infrastructure, data, software, and procedures.",
            required_evidence_types=["pull_request", "jira_issue", "code_review"],
            artifact_count=0,
            approved_count=0,
            coverage_status="missing",
        ),
        ControlResponse(
            id="cc7.2",
            framework=Framework.SOC2,
            control_id="CC7.2",
            title="Change Testing",
            description="Changes are tested before being implemented into production.",
            required_evidence_types=["pull_request", "code_review"],
            artifact_count=0,
            approved_count=0,
            coverage_status="missing",
        ),
        ControlResponse(
            id="cc7.3",
            framework=Framework.SOC2,
            control_id="CC7.3",
            title="Change Approval",
            description="Changes are approved by management before implementation.",
            required_evidence_types=["jira_issue", "code_review", "document"],
            artifact_count=0,
            approved_count=0,
            coverage_status="missing",
        ),
    ]
    return ControlListResponse(controls=change_mgmt_controls, total=len(change_mgmt_controls))


@router.get("/{control_id}", response_model=ControlResponse)
async def get_control(
    control_id: str,
    org_id: CurrentOrgId,
    db: DbSession,
) -> ControlResponse:
    """Get control details."""
    # TODO: Fetch from database
    raise NotImplementedError("Control fetch not yet implemented")


@router.get("/{control_id}/evidence")
async def get_control_evidence(
    control_id: str,
    org_id: CurrentOrgId,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    """Get evidence mapped to a specific control."""
    # TODO: Fetch artifacts mapped to this control
    return {"artifacts": [], "total": 0}


@router.get("/{control_id}/gaps", response_model=list[GapResponse])
async def detect_control_gaps(
    control_id: str,
    org_id: CurrentOrgId,
    db: DbSession,
) -> list[GapResponse]:
    """Detect gaps in evidence for a control."""
    # TODO: Implement gap detection logic
    return []

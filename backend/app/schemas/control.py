"""Control and gap detection schemas."""

from datetime import date
from enum import Enum
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema


class Framework(str, Enum):
    """Compliance frameworks."""

    SOC2 = "soc2"
    ISO27001 = "iso27001"


class CoverageStatus(str, Enum):
    """Control evidence coverage status."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    MISSING = "missing"


class GapSeverity(str, Enum):
    """Gap severity levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GapType(str, Enum):
    """Types of evidence gaps."""

    MISSING_EVIDENCE = "missing_evidence"
    MISSING_APPROVAL = "missing_approval"
    INCOMPLETE_PERIOD = "incomplete_period"


# ============ Response Schemas ============


class ControlResponse(BaseSchema):
    """Basic control response."""

    id: UUID
    framework: Framework
    control_id: str = Field(..., description="e.g., CC7.1, A.12.1.1")
    title: str
    description: str
    required_evidence_types: list[str] = []

    # Computed coverage stats
    artifact_count: int = 0
    approved_count: int = 0
    coverage_status: CoverageStatus = CoverageStatus.MISSING


class ControlDetailResponse(ControlResponse):
    """Detailed control with mapped artifacts."""

    evidence_requirements: str | None = None
    guidance: str | None = None

    # Lists of related data
    artifact_ids: list[UUID] = []
    gaps: list["GapResponse"] = []


class ControlListResponse(BaseSchema):
    """List of controls."""

    controls: list[ControlResponse]
    total: int
    framework: Framework | None = None


class GapResponse(BaseSchema):
    """Evidence gap response."""

    control_id: str
    control_name: str
    gap_type: GapType
    severity: GapSeverity
    description: str
    recommended_action: str
    affected_period_start: date | None = None
    affected_period_end: date | None = None


class GapListResponse(BaseSchema):
    """List of gaps with summary."""

    gaps: list[GapResponse]
    total: int
    by_severity: dict[str, int] = Field(
        default_factory=dict,
        description="Count of gaps by severity",
    )


class ControlCoverageMatrix(BaseSchema):
    """Coverage matrix for dashboard."""

    controls: list[ControlResponse]
    period_start: date
    period_end: date
    overall_coverage_percentage: float
    critical_gaps_count: int


# Forward reference update
ControlDetailResponse.model_rebuild()

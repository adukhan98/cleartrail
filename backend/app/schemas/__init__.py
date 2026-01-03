"""Pydantic schemas for API request/response validation."""

from app.schemas.base import (
    BaseSchema,
    TimestampSchema,
    PaginatedResponse,
)
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
)
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    TokenResponse,
)
from app.schemas.integration import (
    IntegrationCreate,
    IntegrationResponse,
    IntegrationListResponse,
    SyncJobResponse,
    AuthUrlResponse,
    OAuthCallback,
    ConnectionTestResponse,
)
from app.schemas.artifact import (
    ArtifactResponse,
    ArtifactDetailResponse,
    ArtifactListResponse,
    ArtifactApprovalRequest,
    ArtifactApprovalResponse,
    ControlMappingResponse,
    ApprovalRecordResponse,
    CoverageReportResponse,
)
from app.schemas.control import (
    ControlResponse,
    ControlListResponse,
    ControlDetailResponse,
    GapResponse,
)
from app.schemas.packet import (
    PacketCreate,
    PacketUpdate,
    PacketResponse,
    PacketDetailResponse,
    PacketListResponse,
    PacketItemResponse,
    NarrativeGenerateRequest,
    NarrativeApproveRequest,
)
from app.schemas.export import (
    ExportRequest,
    ExportJobResponse,
    ManifestResponse,
)

__all__ = [
    # Base
    "BaseSchema",
    "TimestampSchema",
    "PaginatedResponse",
    # Organization
    "OrganizationCreate",
    "OrganizationUpdate",
    "OrganizationResponse",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "TokenResponse",
    # Integration
    "IntegrationCreate",
    "IntegrationResponse",
    "IntegrationListResponse",
    "SyncJobResponse",
    "AuthUrlResponse",
    "OAuthCallback",
    "ConnectionTestResponse",
    # Artifact
    "ArtifactResponse",
    "ArtifactDetailResponse",
    "ArtifactListResponse",
    "ArtifactApprovalRequest",
    "ArtifactApprovalResponse",
    "ControlMappingResponse",
    "ApprovalRecordResponse",
    "CoverageReportResponse",
    # Control
    "ControlResponse",
    "ControlListResponse",
    "ControlDetailResponse",
    "GapResponse",
    # Packet
    "PacketCreate",
    "PacketUpdate",
    "PacketResponse",
    "PacketDetailResponse",
    "PacketListResponse",
    "PacketItemResponse",
    "NarrativeGenerateRequest",
    "NarrativeApproveRequest",
    # Export
    "ExportRequest",
    "ExportJobResponse",
    "ManifestResponse",
]

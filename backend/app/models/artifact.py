"""Evidence artifact, control mapping, and approval models."""

from datetime import date, datetime
from enum import Enum as PyEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ArtifactType(str, PyEnum):
    """Evidence artifact types."""

    PULL_REQUEST = "pull_request"
    COMMIT = "commit"
    CODE_REVIEW = "code_review"
    JIRA_ISSUE = "jira_issue"
    JIRA_COMMENT = "jira_comment"
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    MEETING_NOTES = "meeting_notes"
    POLICY = "policy"


class ApprovalStatus(str, PyEnum):
    """Artifact approval status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MappingSource(str, PyEnum):
    """How the control mapping was created."""

    AUTO = "auto"  # AI-generated
    MANUAL = "manual"  # Human-assigned


class EvidenceArtifact(Base, TimestampMixin):
    """Core evidence artifact model with provenance."""

    __tablename__ = "evidence_artifacts"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    org_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sync_job_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sync_jobs.id", ondelete="SET NULL"),
        index=True,
    )

    # Source provenance (critical for auditability)
    source_system: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_object_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Content integrity
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256

    # Artifact data
    artifact_type: Mapped[ArtifactType] = mapped_column(Enum(ArtifactType), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    normalized_content: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Period coverage (for Type 2 audits)
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)

    # Approval status
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus),
        default=ApprovalStatus.PENDING,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="artifacts")  # noqa: F821
    sync_job: Mapped["SyncJob | None"] = relationship(back_populates="artifacts")  # noqa: F821
    control_mappings: Mapped[list["ControlMapping"]] = relationship(
        back_populates="artifact",
        cascade="all, delete-orphan",
    )
    approvals: Mapped[list["ApprovalRecord"]] = relationship(
        back_populates="artifact",
        cascade="all, delete-orphan",
    )
    packet_items: Mapped[list["PacketItem"]] = relationship(back_populates="artifact")  # noqa: F821

    # Ensure unique artifact per source
    __table_args__ = (
        UniqueConstraint("org_id", "source_system", "source_object_id", name="uq_artifact_source"),
    )


class ControlMapping(Base, TimestampMixin):
    """Mapping between artifacts and controls."""

    __tablename__ = "control_mappings"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    artifact_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("evidence_artifacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    control_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Mapping provenance
    mapping_source: Mapped[MappingSource] = mapped_column(
        Enum(MappingSource),
        nullable=False,
    )
    mapping_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Float)  # 0-1 for AI mappings

    # Relationships
    artifact: Mapped["EvidenceArtifact"] = relationship(back_populates="control_mappings")


class ApprovalRecord(Base, TimestampMixin):
    """Immutable approval record for audit trail."""

    __tablename__ = "approval_records"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    artifact_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("evidence_artifacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Approval details
    approved: Mapped[bool] = mapped_column(nullable=False)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    # Signature for integrity (hash of artifact_id + user_id + approved_at)
    signature_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Relationships
    artifact: Mapped["EvidenceArtifact"] = relationship(back_populates="approvals")
    user: Mapped["User | None"] = relationship(back_populates="approvals")  # noqa: F821

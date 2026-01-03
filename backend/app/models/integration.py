"""Integration and SyncJob models."""

from datetime import datetime
from enum import Enum as PyEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class IntegrationType(str, PyEnum):
    """Supported integration types."""

    GITHUB = "github"
    JIRA = "jira"
    GOOGLE_DRIVE = "google_drive"


class IntegrationStatus(str, PyEnum):
    """Integration connection status."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class SyncJobStatus(str, PyEnum):
    """Sync job status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Integration(Base, TimestampMixin):
    """Source system integration model."""

    __tablename__ = "integrations"

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
    connector_type: Mapped[IntegrationType] = mapped_column(
        Enum(IntegrationType),
        nullable=False,
    )
    status: Mapped[IntegrationStatus] = mapped_column(
        Enum(IntegrationStatus),
        default=IntegrationStatus.DISCONNECTED,
    )

    # Encrypted OAuth credentials (encrypted at rest, stored as base64 string)
    encrypted_credentials: Mapped[str | None] = mapped_column(Text)

    # Integration-specific configuration (repos to sync, projects, folders)
    config: Mapped[dict | None] = mapped_column(JSONB)

    # Tracking
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="integrations")  # noqa: F821
    sync_jobs: Mapped[list["SyncJob"]] = relationship(back_populates="integration")


class SyncJob(Base, TimestampMixin):
    """Evidence sync job model."""

    __tablename__ = "sync_jobs"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    integration_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("integrations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[SyncJobStatus] = mapped_column(
        Enum(SyncJobStatus),
        default=SyncJobStatus.PENDING,
    )

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Results
    artifacts_found: Mapped[int] = mapped_column(Integer, default=0)
    artifacts_created: Mapped[int] = mapped_column(Integer, default=0)
    error_details: Mapped[dict | None] = mapped_column(JSONB)

    # Relationships
    integration: Mapped["Integration"] = relationship(back_populates="sync_jobs")
    artifacts: Mapped[list["EvidenceArtifact"]] = relationship(back_populates="sync_job")  # noqa: F821

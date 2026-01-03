"""Immutable audit log model."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditLog(Base):
    """Immutable audit log for compliance tracking.

    This table is APPEND-ONLY. No updates or deletes are allowed
    via application code to maintain audit integrity.
    """

    __tablename__ = "audit_logs"

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
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )

    # Event details
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Entity reference
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))

    # Change tracking
    previous_value: Mapped[dict | None] = mapped_column(JSONB)
    new_value: Mapped[dict | None] = mapped_column(JSONB)

    # Request context
    ip_address: Mapped[str | None] = mapped_column(String(45))  # IPv6 max length
    user_agent: Mapped[str | None] = mapped_column(String(500))

    # Human-readable description
    description: Mapped[str | None] = mapped_column(Text)


# Event type constants
class AuditEventType:
    """Audit event type constants."""

    # Artifact events
    ARTIFACT_CREATED = "artifact.created"
    ARTIFACT_APPROVED = "artifact.approved"
    ARTIFACT_REJECTED = "artifact.rejected"
    ARTIFACT_MAPPED = "artifact.mapped"

    # Packet events
    PACKET_CREATED = "packet.created"
    PACKET_NARRATIVE_GENERATED = "packet.narrative_generated"
    PACKET_NARRATIVE_APPROVED = "packet.narrative_approved"
    PACKET_EXPORTED = "packet.exported"

    # Integration events
    INTEGRATION_CONNECTED = "integration.connected"
    INTEGRATION_DISCONNECTED = "integration.disconnected"
    INTEGRATION_SYNC_STARTED = "integration.sync_started"
    INTEGRATION_SYNC_COMPLETED = "integration.sync_completed"
    INTEGRATION_SYNC_FAILED = "integration.sync_failed"

    # User events
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"

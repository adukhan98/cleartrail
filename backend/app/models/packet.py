"""Evidence packet model."""

from datetime import date, datetime
from enum import Enum as PyEnum
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class PacketStatus(str, PyEnum):
    """Evidence packet status."""

    DRAFT = "draft"
    NARRATIVE_PENDING = "narrative_pending"
    NARRATIVE_READY = "narrative_ready"
    APPROVED = "approved"
    EXPORTED = "exported"


class EvidencePacket(Base, TimestampMixin):
    """Evidence packet for auditor export."""

    __tablename__ = "evidence_packets"

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
    control_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Packet metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[PacketStatus] = mapped_column(
        Enum(PacketStatus),
        default=PacketStatus.DRAFT,
    )

    # Audit period
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)

    # AI-generated narrative
    ai_narrative: Mapped[str | None] = mapped_column(Text)
    narrative_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    narrative_approved_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    narrative_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Export tracking
    exported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    drive_folder_url: Mapped[str | None] = mapped_column(Text)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="packets")  # noqa: F821
    items: Mapped[list["PacketItem"]] = relationship(
        back_populates="packet",
        cascade="all, delete-orphan",
        order_by="PacketItem.display_order",
    )


class PacketItem(Base):
    """Evidence packet item (artifact reference)."""

    __tablename__ = "packet_items"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    packet_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("evidence_packets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    artifact_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("evidence_artifacts.id", ondelete="CASCADE"),
        nullable=False,
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    packet: Mapped["EvidencePacket"] = relationship(back_populates="items")
    artifact: Mapped["EvidenceArtifact"] = relationship(back_populates="packet_items")  # noqa: F821

"""Organization model."""

from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Organization(Base, TimestampMixin):
    """Organization (tenant) model."""

    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Audit period settings
    audit_period_start: Mapped[str | None] = mapped_column(String(10))  # YYYY-MM-DD
    audit_period_end: Mapped[str | None] = mapped_column(String(10))

    # Relationships
    users: Mapped[list["User"]] = relationship(back_populates="organization")  # noqa: F821
    integrations: Mapped[list["Integration"]] = relationship(back_populates="organization")  # noqa: F821
    artifacts: Mapped[list["EvidenceArtifact"]] = relationship(back_populates="organization")  # noqa: F821
    packets: Mapped[list["EvidencePacket"]] = relationship(back_populates="organization")  # noqa: F821

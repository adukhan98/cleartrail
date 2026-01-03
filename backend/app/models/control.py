"""Control definition model."""

from uuid import UUID, uuid4

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Control(Base, TimestampMixin):
    """Compliance control definition."""

    __tablename__ = "controls"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Control identification
    framework: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # soc2, iso27001
    control_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # CC7.1, A.12.1
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Control pack grouping
    control_pack: Mapped[str | None] = mapped_column(String(100), index=True)  # change_management

    # Evidence requirements
    required_evidence_types: Mapped[list] = mapped_column(JSONB, default=list)

    # Active status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    class Config:
        """Pydantic config."""

        from_attributes = True

"""Control definition model."""

from uuid import UUID, uuid4

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Control(Base):
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

    # Mapping rules for auto-mapping
    mapping_rules: Mapped[dict | None] = mapped_column(JSONB)

    class Config:
        """Pydantic config."""

        from_attributes = True

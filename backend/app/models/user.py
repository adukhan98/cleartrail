"""User model."""

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """User model."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))  # Null if using OAuth

    # External auth provider ID (Clerk, Supabase, etc.)
    external_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)

    # Organization membership
    org_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
    )
    role: Mapped[str] = mapped_column(String(50), default="member")  # owner, admin, member

    # Relationships
    organization: Mapped["Organization | None"] = relationship(back_populates="users")  # noqa: F821
    approvals: Mapped[list["ApprovalRecord"]] = relationship(back_populates="user")  # noqa: F821

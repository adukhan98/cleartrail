"""Organization schemas."""

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema


class OrganizationBase(BaseSchema):
    """Base organization fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$", description="URL-friendly slug")


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""

    pass


class OrganizationUpdate(BaseSchema):
    """Schema for updating an organization."""

    name: str | None = Field(None, min_length=1, max_length=255)
    slug: str | None = Field(None, min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    audit_period_start: date | None = None
    audit_period_end: date | None = None


class OrganizationResponse(OrganizationBase, TimestampSchema):
    """Organization response schema."""

    id: UUID
    audit_period_start: date | None = None
    audit_period_end: date | None = None
    is_active: bool = True


class OrganizationWithStats(OrganizationResponse):
    """Organization with usage statistics."""

    user_count: int = 0
    integration_count: int = 0
    artifact_count: int = 0

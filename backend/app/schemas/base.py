"""Base schema classes and mixins."""

from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode for SQLAlchemy models
        populate_by_name=True,  # Allow population by field name or alias
        str_strip_whitespace=True,  # Strip whitespace from strings
    )


class TimestampSchema(BaseSchema):
    """Schema mixin for created_at/updated_at timestamps."""

    created_at: datetime
    updated_at: datetime


class IDSchema(BaseSchema):
    """Schema mixin for UUID primary key."""

    id: UUID


# Generic type for paginated responses
T = TypeVar("T")


class PaginatedResponse(BaseSchema, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Factory method to create paginated response."""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class MessageResponse(BaseSchema):
    """Simple message response."""

    message: str


class ErrorResponse(BaseSchema):
    """Error response format."""

    detail: str
    error_code: str | None = None

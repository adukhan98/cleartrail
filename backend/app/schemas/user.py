"""User and authentication schemas."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.base import BaseSchema, TimestampSchema


class UserRole(str, Enum):
    """User roles within an organization."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class UserBase(BaseSchema):
    """Base user fields."""

    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., min_length=8, max_length=100)
    org_id: UUID | None = None


class UserUpdate(BaseSchema):
    """Schema for updating a user."""

    name: str | None = Field(None, min_length=1, max_length=255)
    role: UserRole | None = None


class UserResponse(UserBase, TimestampSchema):
    """User response schema."""

    id: UUID
    org_id: UUID | None = None
    role: UserRole = UserRole.MEMBER
    external_auth_id: str | None = None
    is_active: bool = True


class UserLogin(BaseSchema):
    """Login request schema."""

    email: EmailStr
    password: str


class TokenResponse(BaseSchema):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration in seconds")


class TokenRefreshRequest(BaseSchema):
    """Token refresh request."""

    refresh_token: str


class PasswordChangeRequest(BaseSchema):
    """Password change request."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class UserContext(BaseSchema):
    """Current user context for API operations."""

    user_id: UUID
    org_id: UUID | None
    email: str
    role: UserRole

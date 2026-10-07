"""User schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    """Base user schema."""

    username: str = Field(..., min_length=3, max_length=50)
    role: str = Field(default="OPERATOR", pattern="^(ADMIN|OPERATOR)$")


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    role: Optional[str] = Field(None, pattern="^(ADMIN|OPERATOR)$")
    password: Optional[str] = Field(None, min_length=6)


class UserRead(UserBase):
    """Schema for reading a user."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

"""Common schema definitions."""

from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Message(BaseModel):
    """Generic message response."""

    message: str


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int

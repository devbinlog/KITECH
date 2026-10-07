"""Digital twin integration schemas."""

from typing import Any

from pydantic import BaseModel, Field


class P4RPayloadPreview(BaseModel):
    """Preview wrapper for generated P4R payloads."""

    status: str = "success"
    lot_no: str
    generated_at: str
    payload: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    sources: dict[str, Any] = Field(default_factory=dict)

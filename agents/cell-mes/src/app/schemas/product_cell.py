"""Product-level allowed cell contract."""

from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class ProductCellsUpdate(BaseModel):
    cell_ids: list[Annotated[int, Field(strict=True, gt=0)]]

    @field_validator("cell_ids")
    @classmethod
    def unique_cells(cls, value: list[int]) -> list[int]:
        if len(value) != len(set(value)):
            raise ValueError("Duplicate cell IDs")
        return value


class ProductCellsRead(ProductCellsUpdate):
    product_id: int

"""Cell master updates and optimistic equipment membership changes."""

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.equipment import Equipment
from ..models.master import Cell, ProductCell


class CellError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


async def update_cell(db: AsyncSession, cell_id: int, values: dict) -> Cell:
    cell = await db.get(Cell, cell_id)
    if cell is None:
        raise CellError(404, "Cell not found")
    for key, value in values.items():
        setattr(cell, key, value)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise CellError(409, "이미 사용 중인 Cell 코드입니다.") from exc
    await db.refresh(cell)
    return cell


async def assign_equipment_cell(
    db: AsyncSession, equipment_id: int, cell_id: int | None, expected_cell_id: int | None
) -> Equipment:
    equipment = await db.get(Equipment, equipment_id)
    if equipment is None or (equipment.is_deleted and cell_id is not None):
        raise CellError(404, "Equipment not found")
    if cell_id is not None and await db.get(Cell, cell_id) is None:
        raise CellError(404, "Cell not found")
    # Compare-and-set prevents a stale screen from overwriting another assignment.
    result = await db.execute(
        update(Equipment)
        .where(
            Equipment.id == equipment_id,
            Equipment.is_deleted.is_(False) if cell_id is not None else True,
            Equipment.cell_id == expected_cell_id,
        )
        .values(cell_id=cell_id)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        await db.rollback()
        raise CellError(409, "설비 소속이 변경되었습니다. 새로고침 후 다시 지정해주세요.")
    await db.commit()
    await db.refresh(equipment)
    return equipment


async def delete_empty_cell(db: AsyncSession, cell_id: int) -> None:
    cell = await db.get(Cell, cell_id)
    if cell is None:
        raise CellError(404, "Cell not found")
    linked = await db.scalar(select(Equipment.id).where(Equipment.cell_id == cell_id).limit(1))
    if linked is not None:
        raise CellError(409, "연결된 설비가 있어 Cell을 삭제할 수 없습니다. 삭제된 설비의 연결도 확인해주세요.")
    product_link = await db.scalar(select(ProductCell.id).where(ProductCell.cell_id == cell_id).limit(1))
    if product_link is not None:
        raise CellError(409, "제품의 허용 Cell로 지정되어 있어 삭제할 수 없습니다. 제품 연결을 먼저 해제해주세요.")
    await db.delete(cell)
    await db.commit()

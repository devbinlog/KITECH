"""Product cell membership independent of routing replacement."""

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.master import Cell, Product, ProductCell
from .cell_service import CellError


async def get_product_cells(db: AsyncSession, product_id: int) -> list[int]:
    product = await db.get(Product, product_id)
    if product is None or product.is_deleted:
        raise CellError(404, "Product not found")
    return list((await db.scalars(
        select(ProductCell.cell_id).where(ProductCell.product_id == product_id)
        .order_by(ProductCell.cell_id)
    )).all())


async def save_product_cells(db: AsyncSession, product_id: int, cell_ids: list[int]) -> list[int]:
    existing = set(await get_product_cells(db, product_id))
    requested = set(cell_ids)
    found = set((await db.scalars(select(Cell.id).where(Cell.id.in_(requested)))).all())
    if requested - found:
        raise CellError(400, f"Cells not found: {sorted(requested - found)}")
    # Retain unchanged rows (IDs and created_at) and validate before any deletion.
    await db.execute(delete(ProductCell).where(
        ProductCell.product_id == product_id, ProductCell.cell_id.in_(existing - requested)
    ))
    db.add_all([ProductCell(product_id=product_id, cell_id=cell_id)
                for cell_id in sorted(requested - existing)])
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise CellError(409, "Cell 연결이 변경되었습니다. 새로고침 후 다시 저장해주세요.") from exc
    return sorted(requested)

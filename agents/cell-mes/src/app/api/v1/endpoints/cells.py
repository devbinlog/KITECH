"""Cell endpoints: CRUD for manufacturing cells."""

from typing import List

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from ....models.master import Cell
from ....schemas.master import CellCreate, CellRead
from ...deps import DBSession, CurrentUser, AdminUser
from ....services.cell_service import CellError, update_cell, delete_empty_cell

router = APIRouter()


@router.put("/{cell_id}", response_model=CellRead)
async def edit_cell(
    cell_id: int, payload: CellCreate, db: DBSession, current_user: AdminUser
) -> Cell:
    try:
        return await update_cell(db, cell_id, payload.model_dump())
    except CellError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("", response_model=List[CellRead])
async def list_cells(
    db: DBSession,
    current_user: CurrentUser,
) -> List[Cell]:
    """제조 셀 목록 조회.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        셀 목록 (코드순 정렬)

    """
    result = await db.execute(select(Cell).order_by(Cell.code))
    return list(result.scalars().all())


@router.post("", response_model=CellRead, status_code=status.HTTP_201_CREATED)
async def create_cell(
    db: DBSession,
    current_user: CurrentUser,
    cell_in: CellCreate,
) -> Cell:
    """제조 셀 생성.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        cell_in: 셀 데이터 (code, name, location)

    Returns:
        생성된 셀 정보

    Raises:
        HTTPException: 코드 중복 시 400 에러

    """
    # Check for duplicate code
    result = await db.execute(select(Cell).where(Cell.code == cell_in.code))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cell with code '{cell_in.code}' already exists",
        )

    cell = Cell(**cell_in.model_dump())
    db.add(cell)
    await db.commit()
    await db.refresh(cell)
    return cell


@router.get("/{cell_id}", response_model=CellRead)
async def get_cell(
    db: DBSession,
    current_user: CurrentUser,
    cell_id: int,
) -> Cell:
    """제조 셀 단건 조회.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        cell_id: 셀 ID

    Returns:
        셀 정보

    Raises:
        HTTPException: 셀 미존재 시 404 에러

    """
    result = await db.execute(select(Cell).where(Cell.id == cell_id))
    cell = result.scalar_one_or_none()
    if not cell:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cell not found",
        )
    return cell


@router.delete("/{cell_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cell(
    db: DBSession,
    current_user: CurrentUser,
    cell_id: int,
) -> None:
    """제조 셀 삭제.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        cell_id: 셀 ID

    Raises:
        HTTPException: 셀 미존재 시 404 에러

    """
    result = await db.execute(select(Cell).where(Cell.id == cell_id))
    cell = result.scalar_one_or_none()
    if not cell:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cell not found",
        )

    try:
        await delete_empty_cell(db, cell_id)
    except CellError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

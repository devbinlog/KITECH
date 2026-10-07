"""Process Category endpoints: CRUD for process categories."""

from typing import List

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from ....models.master import ProcessCategory
from ....schemas.master import ProcessCategoryCreate, ProcessCategoryRead
from ...deps import DBSession, CurrentUser

router = APIRouter()


@router.get("", response_model=List[ProcessCategoryRead])
async def list_process_categories(
    db: DBSession,
    current_user: CurrentUser,
) -> List[ProcessCategory]:
    """공정 카테고리 목록 조회.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        공정 카테고리 목록 (코드순 정렬)

    """
    result = await db.execute(select(ProcessCategory).order_by(ProcessCategory.code))
    return list(result.scalars().all())


@router.post("", response_model=ProcessCategoryRead, status_code=status.HTTP_201_CREATED)
async def create_process_category(
    db: DBSession,
    current_user: CurrentUser,
    category_in: ProcessCategoryCreate,
) -> ProcessCategory:
    """공정 카테고리 생성.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        category_in: 카테고리 데이터 (code, name)

    Returns:
        생성된 공정 카테고리 정보

    Raises:
        HTTPException: 코드 중복 시 400 에러

    """
    # Check for duplicate code
    result = await db.execute(
        select(ProcessCategory).where(ProcessCategory.code == category_in.code)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Process category with code '{category_in.code}' already exists",
        )

    category = ProcessCategory(**category_in.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.get("/{category_id}", response_model=ProcessCategoryRead)
async def get_process_category(
    db: DBSession,
    current_user: CurrentUser,
    category_id: int,
) -> ProcessCategory:
    """공정 카테고리 단건 조회.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        category_id: 카테고리 ID

    Returns:
        공정 카테고리 정보

    Raises:
        HTTPException: 카테고리 미존재 시 404 에러

    """
    result = await db.execute(select(ProcessCategory).where(ProcessCategory.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process category not found",
        )
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_process_category(
    db: DBSession,
    current_user: CurrentUser,
    category_id: int,
) -> None:
    """공정 카테고리 삭제.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        category_id: 카테고리 ID

    Raises:
        HTTPException: 카테고리 미존재 시 404 에러

    """
    result = await db.execute(select(ProcessCategory).where(ProcessCategory.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process category not found",
        )

    await db.delete(category)
    await db.commit()

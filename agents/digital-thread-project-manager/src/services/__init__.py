from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorGridFSBucket, AsyncIOMotorCollection
from src.services.file import FileService
from src.services.project import ProjectService
from src.services.v3_project import V3ProjectService
from src.database import get_grid_fs, get_project_collection, get_asset_collection
from src.services.asset import AssetService

# asset 테스트용 코드 추가
from src.services.asset_project import AssetProjectService


async def get_file_service(grid_fs: AsyncIOMotorGridFSBucket = Depends(get_grid_fs)):
    return FileService(grid_fs)


async def get_project_service(
    collection: AsyncIOMotorCollection = Depends(get_project_collection),
):
    return ProjectService(collection)


# asset 테스트용 코드 추가
async def get_asset_project_service(
    collection: AsyncIOMotorCollection = Depends(get_project_collection),
):
    return AssetProjectService(collection)


# v3 asset service 추가
async def get_asset_service(
    collection: AsyncIOMotorCollection = Depends(get_asset_collection),
):
    return AssetService(collection)


# v3 project service 추가
async def get_v3_project_service(
    collection: AsyncIOMotorCollection = Depends(get_asset_collection),
):
    return V3ProjectService(collection)

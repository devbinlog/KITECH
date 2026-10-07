from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorGridFSBucket,
    AsyncIOMotorDatabase,
)
from dotenv import load_dotenv
from functools import lru_cache
from fastapi import Depends
import os
from pymongo import ASCENDING

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "iso14649")


@lru_cache()
def get_motor_client() -> AsyncIOMotorClient:
    return AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=3000)


async def get_db() -> AsyncIOMotorDatabase:
    return get_motor_client()[DATABASE_NAME]


async def get_project_collection(db: AsyncIOMotorDatabase = Depends(get_db)):
    return db["projects"]


async def get_grid_fs(db: AsyncIOMotorDatabase = Depends(get_db)):
    return AsyncIOMotorGridFSBucket(db, bucket_name="files")


# v3용 asset collection 추가
async def get_asset_collection(db: AsyncIOMotorDatabase = Depends(get_db)):
    return db["assets"]


# --- 인덱스 유틸 (호출은 main.py/startup에서) ---
async def ensure_asset_indexes(db: AsyncIOMotorDatabase = Depends(get_db)) -> None:
    col = db["assets"]
    await col.create_index(
        [
            ("global_asset_id", ASCENDING),
            ("asset_id", ASCENDING),
            ("type", ASCENDING),
            ("element_id", ASCENDING),
        ],
        unique=True,
        name="uniq_gasset_asset_type_element",
    )
    await col.create_index([("asset_id", ASCENDING)], name="idx_asset_id")
    await col.create_index([("type", ASCENDING)], name="idx_type")
    await col.create_index([("category", ASCENDING)], name="idx_category")
    await col.create_index([("element_id", ASCENDING)], name="idx_element_id")

from io import BytesIO
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from bson import ObjectId


# GridFS를 이용한 파일 저장/조회/삭제/존재확인 등 파일 관련 DB 작업을 담당하는 클래스입니다.
class FileRepository:
    def __init__(self, grid_fs: AsyncIOMotorGridFSBucket):
        """
        Args:
            grid_fs (AsyncIOMotorGridFSBucket): MongoDB GridFS 버킷 객체
        """
        self.grid_fs = grid_fs

    async def insert_file(
        self, step_file_content: bytes, filename: str, metadata: Optional[dict] = None
    ):
        """
        파일을 GridFS에 업로드하고, 업로드된 파일의 ObjectId를 반환합니다.

        Args:
            step_file_content (bytes): 업로드할 파일 데이터
            filename (str): 저장 파일명
            metadata (dict, optional): 추가 메타데이터

        Returns:
            str: 업로드된 파일의 ObjectId (문자열)
        """
        file_id = await self.grid_fs.upload_from_stream(
            filename, step_file_content, metadata=metadata or {}
        )
        return str(file_id)

    async def get_file(self, file_id: str):
        """
        파일 ObjectId로 GridFS에서 파일 스트림을 조회합니다.

        Args:
            file_id (str): 조회 대상 파일 ObjectId (문자열)

        Returns:
            MotorGridOut: GridFS에서 읽은 파일 스트림
        """
        file_stream = await self.grid_fs.open_download_stream(ObjectId(file_id))
        return file_stream

    async def delete_file_by_id(self, file_id: str):
        """
        파일 ObjectId로 GridFS에서 파일을 삭제합니다.

        Args:
            file_id (str): 삭제할 파일 ObjectId (문자열)
        """
        await self.grid_fs.delete(ObjectId(file_id))
        return

    async def file_exists(self, file_id: str) -> bool:
        """
        파일 존재 여부를 반환합니다.

        Args:
            file_id (str): 확인 대상 파일 ObjectId

        Returns:
            bool: 존재하면 True, 아니면 False
        """
        cursor = self.grid_fs.find({"_id": ObjectId(file_id)}, limit=1)
        docs = await cursor.to_list(length=1)
        return len(docs) > 0

    async def get_file_byteio(self, file_id: str) -> BytesIO:
        """
        파일 ObjectId로 GridFS에서 파일을 읽어 BytesIO 객체로 반환합니다.

        Args:
            file_id (str): 조회할 파일 ObjectId

        Returns:
            BytesIO: 파일 데이터가 담긴 BytesIO 객체
        """
        file_id = ObjectId(file_id)
        grid_out = await self.grid_fs.open_download_stream(file_id)
        file_bytes = await grid_out.read()
        return BytesIO(file_bytes)

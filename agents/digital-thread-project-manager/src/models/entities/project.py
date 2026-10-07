from typing import List
from src.models.schemas.project import ProjectCreateResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId


# 프로젝트 정보를 MongoDB에 저장, 조회, 수정, 삭제 등 프로젝트 관련 DB 작업을 담당하는 클래스입니다.
class ProjectRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Args:
            db (AsyncIOMotorDatabase): MongoDB 데이터베이스 객체
        """
        self.project_collection = db["projects"]

    async def insert_project(
        self, xml_string: str, its_id: str
    ) -> ProjectCreateResponse:
        """
        프로젝트를 신규로 생성하여 MongoDB에 저장합니다.

        Args:
            xml_string (str): 프로젝트 원본 데이터(XML 등)
            its_id (str): 프로젝트명 또는 식별자

        Returns:
            ProjectCreateResponse: 생성된 프로젝트의 ID 반환
        """
        project_data = {"data": xml_string, "name": its_id}
        result = await self.project_collection.insert_one(project_data)
        return ProjectCreateResponse(project_id=str(result.inserted_id))

    async def get_project_list(self) -> List[dict]:
        """
        전체 프로젝트 목록을 조회합니다.

        Returns:
            List[dict]: 프로젝트 정보 리스트
        """
        cursor = self.project_collection.find({})
        projects = await cursor.to_list(length=None)
        return projects

    async def get_dtasset_project_list(self) -> List[dict]:
        """
        전체 프로젝트 목록을 조회합니다.
        dt_asset 프로젝트만 가져올 수 있게 find로 필터링

        Returns:
            List[dict]: 프로젝트 정보 리스트
        """
        cursor = self.project_collection.find(
            {"data": {"$regex": r"<\s*dt_asset(\s|>)", "$options": "i"}},
            projection={"_id": 1},
        )
        projects = await cursor.to_list(length=None)
        return projects

    async def delete_project_by_id(self, project_id: str) -> bool:
        """
        프로젝트 ID로 프로젝트를 삭제합니다.

        Args:
            project_id (str): 삭제할 프로젝트의 ObjectId

        Returns:
            bool: 삭제 성공 시 True
        """
        result = await self.project_collection.delete_one({"_id": ObjectId(project_id)})
        return result.deleted_count > 0

    async def get_project_by_id(self, project_id: str):
        """
        프로젝트 ID로 프로젝트 정보를 조회합니다.

        Args:
            project_id (str): 조회할 프로젝트의 ObjectId

        Returns:
            dict or None: 프로젝트 정보
        """
        return await self.project_collection.find_one({"_id": ObjectId(project_id)})

    async def add_file_to_project(self, project_id: str, file_id: str, file_type: str):
        """
        프로젝트에 파일(ObjectId)를 연결합니다.
        ex) file_type = 'step' 이면, 'step_id' 필드에 파일 추가

        Args:
            project_id (str): 대상 프로젝트 ID
            file_id (str): 추가할 파일 ID
            file_type (str): 파일 종류(step, cad, gdt 등)

        Returns:
            bool: 업데이트 성공 여부
        """
        update_query = {}
        update_query["$push"] = {f"{file_type}_id": file_id}

        result = await self.project_collection.update_one(
            {"_id": ObjectId(project_id)}, update_query
        )
        return result.modified_count > 0

    async def add_dict_to_project(self, project_id: str, file_dict: dict):
        """
        프로젝트에 여러 속성(dict)을 추가/갱신합니다.

        Args:
            project_id (str): 대상 프로젝트 ID
            file_dict (dict): 추가할 데이터 딕셔너리

        Returns:
            bool: 업데이트 성공 여부
        """
        update_query = {"$set": file_dict}
        result = await self.project_collection.update_one(
            {"_id": ObjectId(project_id)}, update_query
        )
        return result.modified_count > 0

    async def update_project_data(self, project_id: str, updated_data: str):
        """
        프로젝트의 data(원본 XML 등) 필드를 업데이트합니다.

        Args:
            project_id (str): 대상 프로젝트 ID
            updated_data (str): 갱신할 데이터

        Returns:
            bool: 업데이트 성공 여부
        """
        result = await self.project_collection.update_one(
            {"_id": ObjectId(project_id)}, {"$set": {"data": updated_data}}
        )
        return result.modified_count > 0

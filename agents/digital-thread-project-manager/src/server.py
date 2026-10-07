from typing import Any
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi_mcp import FastApiMCP
import uvicorn
from contextlib import asynccontextmanager
from bson import ObjectId
from starlette.datastructures import UploadFile
from io import BytesIO

from src.database import get_db, ensure_asset_indexes
from src.services.v3_project import V3ProjectService
from src.services.file import FileService
from src.services import AssetService
from src.services.cam_logic import execute_apply_cam
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from src.utils.exceptions import CustomException

def serialize_mongo(obj):
    if isinstance(obj, dict):
        return {k: serialize_mongo(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_mongo(i) for i in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    return obj

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        db = await get_db()
        await ensure_asset_indexes(db)
    except Exception as e:
        import logging
        logging.warning(f"[lifespan] MongoDB startup check failed (non-fatal): {e}")
    yield

app = FastAPI(lifespan=lifespan)

@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": serialize_mongo(exc.detail)}
    )

@app.get("/health", tags=["meta"])
async def health() -> dict:
    """Liveness probe."""
    return {"status": "ok", "service": "dtp", "version": "0.1.0"}


@app.get("/capabilities", tags=["meta"])
async def capabilities() -> dict:
    """Expose tools for agent-orchestrator's dynamic tool_loader."""
    return {
        "service": "dtp",
        "version": "0.1.0",
        "description": "Digital Thread Project Manager — project creation, CAM parsing, file registration",
        "tools": [
            {
                "name": "get_projects",
                "description": "List recently created Digital Thread projects from local DB.",
                "endpoint": {"method": "GET", "path": "/tools/get_projects"},
                "idempotent": True,
            },
            {
                "name": "create_project",
                "description": "Create a new Digital Thread project from an XML string.",
                "endpoint": {"method": "POST", "path": "/tools/create_project"},
                "idempotent": False,
            },
            {
                "name": "upload_project_to_dp",
                "description": "Upload an existing project and its references to the Nexmoa Data Platform.",
                "endpoint": {"method": "POST", "path": "/tools/upload_project_to_dp"},
                "idempotent": False,
            },
            {
                "name": "upload_nc_file",
                "description": "Upload a physical NC file to GridFS and register it as a dt_file asset.",
                "endpoint": {"method": "POST", "path": "/tools/upload_nc_file"},
                "idempotent": False,
            },
            {
                "name": "attach_project_ref",
                "description": "Attach an uploaded dt_file or other asset reference to a project workplan.",
                "endpoint": {"method": "POST", "path": "/tools/attach_project_ref"},
                "idempotent": False,
            },
            {
                "name": "upload_and_attach_file",
                "description": "Upload a local file and attach it to the target project (e.g. thumbnails, NC, STP).",
                "endpoint": {"method": "POST", "path": "/tools/upload_and_attach_file"},
                "idempotent": False,
            },
            {
                "name": "apply_cam_json",
                "description": "Parse CAM files and append workingsteps to the project Workplan based on a mapping JSON.",
                "endpoint": {"method": "POST", "path": "/tools/apply_cam_json"},
                "idempotent": False,
            },
            {
                "name": "create_asset",
                "description": "Create or upsert any dt_asset (dt_material, dt_machine_tool, dt_file, etc.) from an XML string.",
                "endpoint": {"method": "POST", "path": "/tools/create_asset"},
                "idempotent": True,
            },
        ],
    }


@app.post("/tools/upload_project_to_dp", tags=["4. External Sync (Data Platform)"], summary="Upload project to DP", description="Uploads an existing project to the Nexmoa Data Platform.")
async def upload_project_to_dp_tool(global_asset_id: str, asset_id: str, project_element_id: str) -> Any:
    """Upload an existing project and its references from the local DB to the remote Data Platform (Nexmoa)."""
    db = await get_db()
    project_service = V3ProjectService(db["assets"])
    file_service = FileService(AsyncIOMotorGridFSBucket(db, bucket_name="files"))
    result = await project_service.upload_project_and_related(
        global_asset_id=global_asset_id,
        asset_id=asset_id,
        project_element_id=project_element_id,
        file_service=file_service,
        include_ref_types=None
    )
    return result

@app.post("/tools/create_project", tags=["1. Project Creation"], summary="Create a new project from XML string", description="Creates a new Digital Thread project from the provided XML.")
async def create_project_tool(xml_string: str) -> Any:
    """Create a new project from XML string and save it to the local Mongo database."""
    db = await get_db()
    project_service = V3ProjectService(db["assets"])
    result = await project_service.create_from_xml(xml_string)
    return result

@app.post("/tools/create_asset", tags=["1. Project Creation"], summary="Create or upsert any dt_asset from XML string", description="Creates or upserts a dt_asset of any type (dt_material, dt_machine_tool, dt_file, etc.) from the provided XML.")
async def create_asset_tool(xml_string: str) -> Any:
    """Create or upsert a dt_asset of any type from XML string."""
    db = await get_db()
    asset_service = AssetService(db["assets"])
    result = await asset_service.create_from_xml(xml_string, upsert=True)
    return serialize_mongo(result.model_dump() if hasattr(result, "model_dump") else result)


@app.get("/tools/get_projects", tags=["1. Project Creation"], summary="List created projects", description="Retrieve the list of recently created projects from the local DB.")
async def get_projects_tool() -> Any:
    """Fetch recent projects created in the local MongoDB."""
    db = await get_db()
    cursor = db["assets"].find({"type": "dt_project"}).sort("_id", -1).limit(10)
    projects = await cursor.to_list(length=10)
    return {"count": len(projects), "projects": serialize_mongo(projects)}

@app.post("/tools/upload_nc_file", tags=["3. File Registration (NC, STP)"], summary="Upload NC File to DB", description="Uploads a physical NC file to GridFS and creates a dt_file Asset.")
async def upload_nc_file_tool(
    global_asset_id: str,
    asset_id: str,
    element_id: str,
    workplan_id: str,
    nc_file_path: str
) -> Any:
    db = await get_db()
    asset_service = AssetService(db["assets"])
    file_service = FileService(AsyncIOMotorGridFSBucket(db, bucket_name="files"))
    with open(nc_file_path, "rb") as f:
        content = f.read()
    dummy_file = UploadFile(filename=os.path.basename(nc_file_path), file=BytesIO(content))
    result = await asset_service.create_nc_dt_file_from_upload(
        global_asset_id=global_asset_id,
        project_asset_id=asset_id,
        project_element_id=element_id,
        workplan_id=workplan_id,
        file=dummy_file,
        file_service=file_service
    )
    return serialize_mongo(result.model_dump() if hasattr(result, "model_dump") else result)

@app.post("/tools/attach_project_ref", tags=["3. File Registration (NC, STP)"], summary="Attach an asset reference to a project", description="Attaches an uploaded dt_file or other asset to a project/workplan.")
async def attach_project_ref_tool(
    global_asset_id: str,
    asset_id: str,
    project_element_id: str,
    ref_global_asset_id: str,
    ref_asset_id: str,
    ref_element_id: str,
    ref_type: str,
    ref_category: str = None,
    workplan_id: str = None,
    workpiece_id: str = None,
    workingstep_id: str = None
) -> Any:
    db = await get_db()
    project_service = V3ProjectService(db["assets"])
    result = await project_service.attach_ref(
        global_asset_id=global_asset_id,
        asset_id=asset_id,
        project_element_id=project_element_id,
        ref_global_asset_id=ref_global_asset_id,
        ref_asset_id=ref_asset_id,
        ref_element_id=ref_element_id,
        ref_type=ref_type,
        ref_category=ref_category,
        workplan_id=workplan_id,
        workpiece_id=workpiece_id,
        workingstep_id=workingstep_id
    )
    return serialize_mongo(result)

from pydantic import BaseModel
import uuid

class ApplyCamJsonRequest(BaseModel):
    global_asset_id: str
    asset_id: str
    project_element_id: str
    workplan_id: str
    cam_type: str
    cam_files: list[str]
    mapping_file: str
    ops_order: str = None

class UploadAndAttachFileRequest(BaseModel):
    global_asset_id: str
    asset_id: str
    project_element_id: str
    workplan_id: str
    file_path: str
    ref_type: str = "dt_file"
    ref_category: str = "general_file"

@app.post("/tools/upload_and_attach_file", tags=["3. File Registration (NC, STP)"], summary="Upload and Attach General File", description="Uploads a local file and attaches it to the target project (e.g., Thumbnails, NC, STP).")
async def upload_and_attach_file_tool(req: UploadAndAttachFileRequest) -> Any:
    db = await get_db()
    asset_service = AssetService(db["assets"])
    file_service = FileService(AsyncIOMotorGridFSBucket(db, bucket_name="files"))
    project_service = V3ProjectService(db["assets"])
    
    if not os.path.exists(req.file_path):
        raise CustomException(status_code=400, detail={"message": f"File not found: {req.file_path}"})
        
    filename = os.path.basename(req.file_path)
    with open(req.file_path, "rb") as f:
        file_bytes = f.read()
    
    dummy_file = UploadFile(filename=filename, file=BytesIO(file_bytes))
    file_oid = await file_service.process_upload(dummy_file)
    
    file_element_id = f"file_{uuid.uuid4().hex[:8]}"
    ref_asset_id = f"{req.asset_id}_attachment"
    
    dt_file_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<dt_asset xmlns="http://digital-thread.re/dt_asset" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" schemaVersion="v31">
  <asset_global_id>{req.global_asset_id}</asset_global_id>
  <id>{ref_asset_id}</id>
  <asset_kind>instance</asset_kind>
  <dt_elements xsi:type="dt_file">
    <element_id>{file_element_id}</element_id>
    <category>{req.ref_category}</category>
    <display_name>{filename}</display_name>
    <content_type>application/octet-stream</content_type>
    <value>{file_oid}</value>
  </dt_elements>
</dt_asset>"""

    await asset_service.create_from_xml(dt_file_xml, upsert=True)
    
    result = await project_service.attach_ref(
        global_asset_id=req.global_asset_id,
        asset_id=req.asset_id,
        project_element_id=req.project_element_id,
        ref_global_asset_id=req.global_asset_id,
        ref_asset_id=ref_asset_id,
        ref_element_id=file_element_id,
        ref_type=req.ref_type,
        ref_category=req.ref_category,
        workplan_id=req.workplan_id
    )
    return serialize_mongo(result)

@app.post("/tools/apply_cam_json", tags=["2. CAM Parsing"], summary="Apply CAM JSON to Project", description="Generates cutting tool XMLs and appends workingsteps to the Workplan based on CAM file and Mapping JSON.")
async def apply_cam_json_tool(req: ApplyCamJsonRequest) -> Any:
    db = await get_db()
    asset_service = AssetService(db["assets"])
    file_service = FileService(AsyncIOMotorGridFSBucket(db, bucket_name="files"))
    project_service = V3ProjectService(db["assets"])
    result = await execute_apply_cam(
        global_asset_id=req.global_asset_id,
        asset_id=req.asset_id,
        project_element_id=req.project_element_id,
        workplan_id=req.workplan_id,
        cam_type=req.cam_type,
        cam_files=req.cam_files,
        mapping_file=req.mapping_file,
        asset_service=asset_service,
        file_service=file_service,
        project_service=project_service,
        ops_order=req.ops_order
    )
    return serialize_mongo(result)

mcp = FastApiMCP(app, name="Digital Thread Project Manager MCP Server", description="Provides tools for orchestrator to create and upload projects.")
mcp.mount()

if __name__ == "__main__":
    uvicorn.run("src.server:app", host="0.0.0.0", port=8000, reload=True)

"""Files router: NC file management (mock).

Maps TORUS getFileList → GET /api/v1/files
Maps TORUS UploadFile → POST /api/v1/files/upload
Maps TORUS DownloadFile → GET /api/v1/files/download
"""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/v1/files", tags=["files"])

# In-memory mock file system
_mock_files: Dict[int, List[Dict[str, Any]]] = {
    1: [
        {
            "name": "O0001",
            "path": "//CNC_MEM/O0001",
            "size": 1024,
            "date": "2025-01-01T00:00:00",
            "type": "program",
        },
        {
            "name": "O0002",
            "path": "//CNC_MEM/O0002",
            "size": 2048,
            "date": "2025-01-15T10:30:00",
            "type": "program",
        },
    ],
    2: [
        {
            "name": "MAIN_MPF",
            "path": "/_N_MPF_DIR/_N_MAIN_MPF",
            "size": 2048,
            "date": "2025-01-15T10:00:00",
            "type": "program",
        },
        {
            "name": "SUB1_SPF",
            "path": "/_N_SPF_DIR/_N_SUB1_SPF",
            "size": 512,
            "date": "2025-02-01T08:00:00",
            "type": "subprogram",
        },
    ],
}


@router.get("")
async def get_file_list(
    machine: int = Query(1, description="Machine ID"),
    path: str = Query("", description="Directory path filter"),
):
    """List NC files on a machine (getFileList)."""
    files = _mock_files.get(machine, [])
    if path:
        files = [f for f in files if path in f.get("path", "")]
    return {"machine": machine, "files": files}


@router.post("/upload")
async def upload_file(
    machine: int = Query(1, description="Machine ID"),
    name: str = Query(..., description="File name"),
    content: str = Query("", description="File content (mock)"),
):
    """Upload NC file to machine (UploadFile) — mock."""
    if machine not in _mock_files:
        _mock_files[machine] = []

    file_entry = {
        "name": name,
        "path": f"//CNC_MEM/{name}",
        "size": len(content),
        "date": "2025-01-01T00:00:00",
        "type": "program",
    }
    _mock_files[machine].append(file_entry)
    return {"success": True, "file": file_entry}


@router.get("/download")
async def download_file(
    machine: int = Query(1, description="Machine ID"),
    name: str = Query(..., description="File name"),
):
    """Download NC file from machine (DownloadFile) — mock."""
    files = _mock_files.get(machine, [])
    file_entry = next((f for f in files if f["name"] == name), None)
    if not file_entry:
        raise HTTPException(status_code=404, detail=f"File '{name}' not found on machine {machine}")

    return {
        "success": True,
        "file": file_entry,
        "content": f"% Mock NC program: {name}\nG0 X0 Y0\nG1 X100 Y100 F500\nM30\n%",
    }

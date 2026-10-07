from pydantic import BaseModel

class FileCreateResponse(BaseModel):
    file_id: str

class StpCreateResponse(BaseModel):
    step_id: str
    stl_id: str
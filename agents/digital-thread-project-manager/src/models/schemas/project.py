from typing import List, Optional
from pydantic import BaseModel, Field

class ProjectCreateResponse(BaseModel):
    project_id: str
    
class ProjectListResponse(BaseModel):
    project_id: Optional[List[str]] = Field(default=[])
    
class ProjectResponse(BaseModel):
    _id: str
    data: str
    step_id: Optional[str] = None
    stl_id: Optional[str] = None
    
class TdmsPahtListResponse(BaseModel):
    tdms_list: List[str]
"""Master data schemas: ProcessCategory, Cell, StdProcess, Product, Routing, Scenario."""

import re
from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Security: Pattern for safe identifiers (alphanumeric, hyphen, underscore only)
SAFE_CODE_PATTERN = re.compile(r"^[A-Za-z0-9_\-]+$")
SAFE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9가-힣\s_\-\.\(\)]+$")
SAFE_PATH_PATTERN = re.compile(r"^[A-Za-z0-9_\-/\.]+$")


def validate_safe_code(value: str, field_name: str = "code") -> str:
    """Validate that a code contains only safe characters."""
    if not SAFE_CODE_PATTERN.match(value):
        raise ValueError(
            f"{field_name} must contain only alphanumeric characters, hyphens, and underscores"
        )
    return value


def validate_safe_name(value: str, field_name: str = "name") -> str:
    """Validate that a name contains only safe characters."""
    if not SAFE_NAME_PATTERN.match(value):
        raise ValueError(
            f"{field_name} must contain only alphanumeric characters, Korean, spaces, hyphens, underscores, dots, and parentheses"
        )
    return value


def validate_safe_path(value: str, field_name: str = "path") -> str:
    """Validate that a path contains only safe characters (no directory traversal)."""
    if ".." in value:
        raise ValueError(f"{field_name} must not contain path traversal sequences")
    if not SAFE_PATH_PATTERN.match(value):
        raise ValueError(
            f"{field_name} must contain only alphanumeric characters, hyphens, underscores, slashes, and dots"
        )
    return value


# ============================================================================
# Process Category (공정 카테고리)
# ============================================================================


class ProcessCategoryBase(BaseModel):
    """Base process category schema."""

    code: str = Field(
        ..., min_length=1, max_length=30, description="카테고리 코드 (MACHINING, ASSEMBLY 등)"
    )
    name: str = Field(
        ..., min_length=1, max_length=50, description="카테고리명 (기계가공, 조립 등)"
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        return validate_safe_code(v, "code")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_safe_name(v, "name")


class ProcessCategoryCreate(ProcessCategoryBase):
    """Schema for creating a process category."""

    pass


class ProcessCategoryRead(ProcessCategoryBase):
    """Schema for reading a process category."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Cell (제조 셀)
# ============================================================================


class CellBase(BaseModel):
    """Base cell schema."""

    code: str = Field(..., min_length=1, max_length=20, description="셀 코드 (CELL-01, CELL-02 등)")
    name: str = Field(..., min_length=1, max_length=100, description="셀명 (CNC 셀 1, 로봇 셀 등)")
    location: Optional[str] = Field(None, max_length=100, description="위치 (A동 1층 등)")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        return validate_safe_code(v, "code")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_safe_name(v, "name")


class CellCreate(CellBase):
    """Schema for creating a cell."""

    pass


class CellRead(CellBase):
    """Schema for reading a cell."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Standard Process (표준 공정)
# ============================================================================


class StdProcessBase(BaseModel):
    """Base standard process schema."""

    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category_id: Optional[int] = Field(default=None, description="공정 카테고리 ID (FK)")
    equipment_type: Optional[str] = Field(default=None, description="설비 유형 (CNC, ROBOT 등)")
    required_machines: Optional[List[str]] = Field(
        default=None, description="기본 설비/장비 후보 목록 (라우팅 오버라이드 없을 시 사용)"
    )
    cycle_time_sec: int = Field(default=60, ge=0, description="단위당 사이클 타임 (초)")
    setup_time_sec: int = Field(default=0, ge=0, description="준비 시간 (초)")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        return validate_safe_code(v, "code")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_safe_name(v, "name")


class StdProcessCreate(StdProcessBase):
    """Schema for creating a standard process."""

    pass


class StdProcessRead(StdProcessBase):
    """Schema for reading a standard process."""

    id: int
    category: Optional[ProcessCategoryRead] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StdProcessUpdate(BaseModel):
    """Schema for updating a standard process."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    equipment_type: Optional[str] = Field(None, max_length=50)
    required_machines: Optional[List[str]] = Field(None, description="기본 설비/장비 후보 목록")
    category_id: Optional[int] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_safe_name(v, "name")
        return v


# ============================================================================
# Product (제품)
# ============================================================================


class ProductBase(BaseModel):
    """Base product schema."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    unit: str = Field(default="EA", max_length=10)

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        return validate_safe_code(v, "code")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_safe_name(v, "name")

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v: str) -> str:
        return validate_safe_code(v, "unit")


class DtProjectSelect(BaseModel):
    """DTP project identity selected by the user."""

    asset_global_id: str = Field(..., max_length=255)
    asset_id: str = Field(..., max_length=255)
    element_id: str = Field(..., max_length=100)
    element_full_id: Optional[str] = Field(default=None, max_length=255)
    element_category: str = Field(default="Project", max_length=50)
    external_project_id: Optional[str] = Field(default=None, max_length=100)
    display_name: Optional[str] = Field(default=None, max_length=255)
    uuid: Optional[str] = Field(default=None, max_length=100)


class DtProjectWorkplanRead(BaseModel):
    """Workplan parsed from linked DT Project XML."""

    id: int
    workplan_id: str
    parent_workplan_id: Optional[str] = None
    display_name: Optional[str] = None
    source_path: str
    level: int
    sequence: int
    has_direct_steps: bool

    model_config = ConfigDict(from_attributes=True)


class DtProjectSummary(BaseModel):
    """Current DT Project link summary for a MES product."""

    id: int
    platform: str
    external_project_id: Optional[str] = None
    asset_global_id: str
    asset_id: str
    element_id: str
    element_full_id: Optional[str] = None
    element_category: str
    display_name: Optional[str] = None
    uuid: Optional[str] = None
    workplans: List[DtProjectWorkplanRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DtProjectLinkRead(BaseModel):
    """Product DT Project link response."""

    product_id: int
    dt_project: Optional[DtProjectSummary] = None


class DtProjectLookupRead(DtProjectSelect):
    """DTP project search item returned to frontend pickers."""

    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class DtFileRefRead(BaseModel):
    """DTP file reference stored in MES."""

    id: int
    platform: str
    external_file_id: str
    asset_global_id: str
    asset_id: Optional[str] = None
    element_id: Optional[str] = None
    element_full_id: Optional[str] = None
    element_category: str
    display_name: Optional[str] = None
    path: str
    references: Optional[dict[str, Any]] = None
    workplan_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(ProductBase):
    """Schema for creating a product."""

    dt_project: Optional[DtProjectSelect] = None


class ProductRead(ProductBase):
    """Schema for reading a product."""

    id: int
    is_deleted: bool
    created_at: datetime
    current_dt_project: Optional[DtProjectSummary] = None

    model_config = ConfigDict(from_attributes=True)


class ProductUpdate(BaseModel):
    """Schema for updating a product."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    unit: Optional[str] = Field(None, max_length=10)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_safe_name(v, "name")
        return v


# Process Routing File
class ProcessRoutingFileBase(BaseModel):
    """Base routing file schema."""

    file_type: str = Field(default="NC", pattern="^(NC|IMAGE|DOC)$")
    file_path: str = Field(..., max_length=255)
    original_filename: Optional[str] = Field(default=None, max_length=255)
    source_type: Literal["LOCAL_UPLOAD", "DTP"] = "LOCAL_UPLOAD"
    dt_file_ref_id: Optional[int] = None
    compatible_machines: Optional[List[str]] = Field(
        default=None, description="이 파일을 실행할 수 있는 장비 후보 목록"
    )
    sort_order: int = Field(default=1, ge=1)

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        return validate_safe_path(v, "file_path")

    @field_validator("original_filename")
    @classmethod
    def validate_original_filename(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if "\x00" in v or "/" in v or "\\" in v:
            raise ValueError("original_filename must be a filename, not a path")
        return v


class ProcessRoutingFileCreate(ProcessRoutingFileBase):
    """Schema for creating a routing file."""

    pass


class ProcessRoutingFileRead(ProcessRoutingFileBase):
    """Schema for reading a routing file."""

    id: int
    process_routing_id: int
    dt_file: Optional[DtFileRefRead] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Process Routing
class ProcessRoutingBase(BaseModel):
    """Base routing schema."""

    std_process_id: int
    sequence: int = Field(..., ge=1)
    revision: str = Field(
        default="A", max_length=10, description="라우팅 버전 (A, B, C 또는 1, 2, 3)"
    )
    setup_id: Optional[str] = Field(
        default=None, max_length=50, description="셋업 ID (같은 장비에서 연속 작업 시 셋업 교체 여부 판단)"
    )
    dt_workplan_id: Optional[int] = Field(
        default=None, description="제품에 연결된 DT Project Workplan ID"
    )
    required_machines: Optional[List[str]] = Field(
        default=None, description="제품/라우팅별 장비 후보 오버라이드"
    )
    cycle_time_sec: Optional[int] = Field(
        default=None,
        ge=0,
        le=2147483647,
        description="제품/라우팅별 사이클 타임 (초). 없으면 표준공정 기본값 사용",
    )
    cycle_time_breakdown: Optional[dict[str, Any]] = Field(
        default=None,
        description="라우팅 사이클 타임 산정 근거 (NC 분석, 내부 action timing 등)",
    )
    remarks: Optional[str] = Field(None, max_length=255)


class ProcessRoutingCreate(ProcessRoutingBase):
    """Schema for creating a routing with files."""

    files: List[ProcessRoutingFileCreate] = Field(default_factory=list)


class ProcessRoutingRead(ProcessRoutingBase):
    """Schema for reading a routing."""

    id: int
    product_id: int
    revision: str = "A"
    files: List[ProcessRoutingFileRead] = Field(default_factory=list)
    std_process: Optional[StdProcessRead] = None
    dt_workplan: Optional[DtProjectWorkplanRead] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Scenario
class ScenarioBase(BaseModel):
    """Base scenario schema."""

    code: str = Field(..., min_length=1, max_length=20, description="시나리오 코드 (SCN-001)")
    name: str = Field(..., min_length=1, max_length=100)
    file_path: str = Field(..., max_length=255)
    is_active: bool = Field(default=True)

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        return validate_safe_code(v, "code")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_safe_name(v, "name")

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        return validate_safe_path(v, "file_path")


class ScenarioCreate(ScenarioBase):
    """Schema for creating a scenario."""

    product_id: Optional[int] = None


class ScenarioRead(ScenarioBase):
    """Schema for reading a scenario."""

    id: int
    code: str
    product_id: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScenarioUpdate(BaseModel):
    """Schema for updating a scenario."""

    code: Optional[str] = Field(None, min_length=1, max_length=20)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    file_path: Optional[str] = Field(None, max_length=255)
    product_id: Optional[int] = None
    is_active: Optional[bool] = None

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_safe_code(v, "code")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_safe_name(v, "name")
        return v

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_safe_path(v, "file_path")
        return v


# ============================================================================
# Scenario Content (YAML 본문 편집) — n8n YAML editor integration M0
# Design Ref: §4 API Specification (PUT content), §3 Data Model
# ============================================================================


class ScenarioContentUpdate(BaseModel):
    """Schema for PUT /scenarios/{id}/content — YAML text payload.

    Frontend converts n8n workflow JSON to YAML text via
    /api/v1/converters/n8n-to-yaml, then submits the YAML string here.
    Server validates with yaml.safe_load and writes to file_path.
    """

    content: str = Field(
        ...,
        min_length=1,
        max_length=1_048_576,  # 1MB
        description="시나리오 YAML 텍스트 (UTF-8)",
    )


class ScenarioContentSaveResponse(BaseModel):
    """Response for PUT /scenarios/{id}/content."""

    id: int
    file_path: str
    size_bytes: int
    saved_at: datetime
    backup_created: bool


class ActionCatalogItem(BaseModel):
    """Single action entry for ScenarioStep action dropdown.

    Used by Expression autocomplete and Step parameter form.
    Plan SC: #7 (action 카탈로그)
    """

    key: str = Field(..., description="템플릿 키 (예: '{{acq.main}}/api/move')")
    category: str = Field(..., description="카테고리 (robot, gripper, cnc, util)")
    description: str = Field(..., description="짧은 설명")


class ActionCatalogResponse(BaseModel):
    """Response for GET /scenarios/actions."""

    data: List[ActionCatalogItem]


# ============================================================================
# Test Execution (M9 — n8n YAML editor integration)
# ============================================================================


class TestRunCreateRequest(BaseModel):
    """POST /scenarios/{id}/test-runs body."""

    workflow: dict = Field(
        ...,
        description="n8n workflow JSON (nodes, connections, ...)",
    )


class TestRunCreateResponse(BaseModel):
    """POST /scenarios/{id}/test-runs response."""

    execution_id: str
    status: str = Field(..., description="queued | running | error")


class NodeExecutionState(BaseModel):
    """Per-node execution result."""

    status: str = Field(..., description="pending | running | success | error")
    input: Optional[dict] = None
    output: Optional[dict] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None


class TestRunStatusResponse(BaseModel):
    """GET /scenarios/test-runs/{execution_id} response."""

    execution_id: str
    status: str = Field(
        ...,
        description="queued | running | success | error | cancelled",
    )
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    nodes: dict = Field(default_factory=dict)


class TestRunCancelResponse(BaseModel):
    """POST /scenarios/test-runs/{execution_id}/cancel response."""

    execution_id: str
    status: str

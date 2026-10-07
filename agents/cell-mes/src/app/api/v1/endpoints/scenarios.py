"""Scenario management endpoints.

Design Ref: §4 API Specification
  - GET /content (existing — parsed dict)
  - PUT /content (M0 — YAML text save with .bak backup)
  - GET /actions (M0 — action catalog for Step parameter dropdown)

Plan SC: #2 (편집/저장 동등), #7 (action 카탈로그), #8 (validation 응답), #9 (sticky 보존)
"""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import yaml
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select

from ....models.master import Scenario, Product
from ....schemas.master import (
    ActionCatalogResponse,
    ScenarioContentSaveResponse,
    ScenarioContentUpdate,
    ScenarioCreate,
    ScenarioRead,
    ScenarioUpdate,
    TestRunCancelResponse,
    TestRunCreateRequest,
    TestRunCreateResponse,
    TestRunStatusResponse,
)
from ...deps import DBSession, CurrentUser
from ....core.config import settings
from ....services.scenario_actions_catalog import get_actions
from ....services import n8n_runner  # noqa: E402 — safe; runs after services/__init__

router = APIRouter()


_PROJECT_ROOT = Path(__file__).resolve().parents[6]


def _is_within(candidate: Path, base: Path) -> bool:
    """Return True iff resolved `candidate` is inside resolved `base` (traversal-safe).

    Uses `Path.is_relative_to` (Python 3.9+) on resolved paths so symlink and
    `..` tricks cannot escape the allowed roots.
    """
    try:
        return candidate.resolve().is_relative_to(base.resolve())
    except (OSError, ValueError):
        return False


def _resolve_scenario_file_path(file_path: str) -> Path:
    """Resolve a `scenario.file_path` to an absolute Path with traversal protection.

    Allowed roots (in priority order):
      1. `settings.SCENARIOS_DIR` (or project_root/samples/scenarios as default)
      2. `project_root` (legacy fallback used by handover migration)

    Reject any input that resolves outside both roots — even when the rejected
    path resembles `../../../etc/passwd` or an absolute path that escapes.

    Design Ref: §4 (PUT content path resolution shared with GET).
    Security:   security-reviewer C2 — CWE-22 path traversal mitigation.
    """
    if not file_path or not isinstance(file_path, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file_path is required",
        )

    # Reject NUL bytes outright (filesystem layer would silently truncate on POSIX).
    if "\x00" in file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file_path: NUL byte",
        )

    file_path_str = file_path.lstrip("/")

    # Roots
    scenarios_dir = getattr(settings, "SCENARIOS_DIR", None)
    primary_root = (
        Path(scenarios_dir).resolve()
        if scenarios_dir
        else (_PROJECT_ROOT / "samples" / "scenarios").resolve()
    )
    fallback_root = _PROJECT_ROOT.resolve()

    # Try primary root first
    primary_candidate = (primary_root / file_path_str)
    if _is_within(primary_candidate, primary_root):
        if primary_candidate.exists():
            return primary_candidate
        # Resolve to absolute even if not yet existing (PUT-create allowed only if inside root).
        primary_target = primary_candidate.resolve()
        # Existence test was negative — fall through to fallback root.
    else:
        # Path escapes primary root — refuse immediately.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file_path: outside allowed scenarios directory",
        )

    # Fallback: project-root relative (legacy, e.g. "cell-mes/data/foo.yaml").
    fallback_candidate = (fallback_root / file_path_str)
    if not _is_within(fallback_candidate, fallback_root):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file_path: outside allowed roots",
        )
    if fallback_candidate.exists():
        return fallback_candidate

    # Neither location holds the file yet — return the primary candidate (PUT will create).
    return primary_target


@router.get("", response_model=List[ScenarioRead])
async def list_scenarios(
    db: DBSession,
    current_user: CurrentUser,
    product_id: int = None,
    active_only: bool = True,
) -> List[Scenario]:
    """List scenarios, optionally filtered by product."""
    query = select(Scenario).order_by(Scenario.name)

    if product_id is not None:
        query = query.where(Scenario.product_id == product_id)

    if active_only:
        query = query.where(Scenario.is_active.is_(True))

    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("", response_model=ScenarioRead, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    db: DBSession,
    current_user: CurrentUser,
    scenario_in: ScenarioCreate,
) -> Scenario:
    """Create a new scenario."""
    # Validate product_id if provided
    if scenario_in.product_id:
        result = await db.execute(select(Product).where(Product.id == scenario_in.product_id))
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product not found",
            )

    scenario = Scenario(**scenario_in.model_dump())
    db.add(scenario)
    await db.commit()
    await db.refresh(scenario)
    return scenario


@router.get("/actions", response_model=ActionCatalogResponse)
async def list_action_catalog(
    current_user: CurrentUser,
) -> ActionCatalogResponse:
    """Return the static action template catalog.

    Defined BEFORE GET /{scenario_id} to avoid path-int conversion error.

    Design Ref: §4 GET /scenarios/actions
    Plan SC: #7 (expression suggestion)
    """
    return ActionCatalogResponse(data=get_actions())


@router.get("/{scenario_id}", response_model=ScenarioRead)
async def get_scenario(
    db: DBSession,
    current_user: CurrentUser,
    scenario_id: int,
) -> Scenario:
    """Get a scenario by ID."""
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found",
        )
    return scenario


@router.get("/{scenario_id}/content")
async def get_scenario_content(
    db: DBSession,
    current_user: CurrentUser,
    scenario_id: int,
) -> Dict[str, Any]:
    """Get scenario control file content (JSON)."""
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found",
        )

    # Get scenarios directory from settings or use default
    scenarios_dir = getattr(settings, "SCENARIOS_DIR", None)
    if scenarios_dir:
        base_path = Path(scenarios_dir)
    else:
        # Default to workspace samples directory
        base_path = (
            Path(__file__).parent.parent.parent.parent.parent.parent.parent
            / "samples"
            / "scenarios"
        )

    # Construct file path
    file_path_str = scenario.file_path.lstrip("/")
    file_path = base_path / file_path_str

    # Try alternative path if not found
    if not file_path.exists():
        # Try relative to project root
        alt_path = Path(__file__).parent.parent.parent.parent.parent.parent.parent / file_path_str
        if alt_path.exists():
            file_path = alt_path

    content = None
    if file_path.exists():
        try:
            with open(file_path, encoding="utf-8") as f:
                if file_path.suffix.lower() in [".yaml", ".yml"]:
                    import yaml
                    content = yaml.safe_load(f)
                else:
                    content = json.load(f)
        except Exception as e:
            # Continue to middleware fallback if local read fails
            pass

    # Fallback to Middleware API if not found locally or failed to read
    if content is None:
        try:
            import httpx
            middleware_url = settings.MIDDLEWARE_URL.rstrip("/")
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{middleware_url}/api/recipes/{file_path_str}")
                if res.status_code == 200:
                    # Check if response is YAML or JSON
                    try:
                        recipe_res = res.json()
                        if isinstance(recipe_res, dict) and recipe_res.get("status") == "success":
                            content = recipe_res.get("data")
                        else:
                            content = recipe_res
                    except (json.JSONDecodeError, ValueError):
                        # Not JSON, try parsing as YAML
                        import yaml
                        content = yaml.safe_load(res.text)
        except Exception as e:
            return {
                "error": f"File not found locally and middleware fetch failed: {str(e)}",
                "path": scenario.file_path,
                "searched_paths": [str(base_path / file_path_str)],
            }

    if content is None:
        return {
            "error": "File not found",
            "path": scenario.file_path,
            "searched_paths": [str(base_path / file_path_str)],
        }

    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario.name,
        "file_path": scenario.file_path,
        "content": content,
    }


@router.get("/{scenario_id}/download")
async def download_scenario_file(
    db: DBSession,
    current_user: CurrentUser,
    scenario_id: int,
) -> PlainTextResponse:
    """Return the raw scenario control file as inline text.

    Middleware can read the response body directly without saving an attachment.
    """
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found",
        )

    file_path = _resolve_scenario_file_path(scenario.file_path)
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario file not found on disk",
        )

    return PlainTextResponse(
        content=file_path.read_text(encoding="utf-8"),
        media_type="text/yaml",
    )


@router.patch("/{scenario_id}", response_model=ScenarioRead)
async def update_scenario(
    db: DBSession,
    current_user: CurrentUser,
    scenario_id: int,
    scenario_in: ScenarioUpdate,
) -> Scenario:
    """시나리오 정보 부분 수정 (이름, 파일 경로, 제품 연결 등)."""
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found",
        )

    # product_id 유효성 검증 (값이 전달된 경우)
    if scenario_in.product_id is not None:
        prod_result = await db.execute(select(Product).where(Product.id == scenario_in.product_id))
        if not prod_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product not found",
            )

    # None이 아닌 필드만 업데이트
    update_data = scenario_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(scenario, field, value)

    await db.commit()
    await db.refresh(scenario)
    return scenario


@router.patch("/{scenario_id}/active", response_model=ScenarioRead)
async def toggle_scenario_active(
    db: DBSession,
    current_user: CurrentUser,
    scenario_id: int,
    is_active: bool,
) -> Scenario:
    """Toggle scenario active status."""
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found",
        )

    scenario.is_active = is_active
    await db.commit()
    await db.refresh(scenario)
    return scenario


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(
    db: DBSession,
    current_user: CurrentUser,
    scenario_id: int,
) -> None:
    """Delete a scenario."""
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found",
        )

    await db.delete(scenario)
    await db.commit()


# ============================================================================
# n8n YAML editor integration (M0)
# ============================================================================


@router.put(
    "/{scenario_id}/content",
    response_model=ScenarioContentSaveResponse,
)
async def save_scenario_content(
    db: DBSession,
    current_user: CurrentUser,
    scenario_id: int,
    payload: ScenarioContentUpdate,
) -> ScenarioContentSaveResponse:
    """Save scenario YAML text to disk.

    Frontend posts the YAML string converted from n8n workflow JSON via
    /api/v1/converters/n8n-to-yaml. Server validates with yaml.safe_load,
    creates a single .bak generation, then writes to scenario.file_path.

    Design Ref: §4 PUT /scenarios/{id}/content
    Plan SC: #2 (편집/저장 동등), #8 (validation 응답)
    """
    # 1. Lookup scenario
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found",
        )

    # 2. Validate YAML structurally before any disk write
    try:
        parsed = yaml.safe_load(payload.content)
    except yaml.YAMLError as exc:
        # Extract line/column from yaml's MarkedYAMLError when available
        details: Dict[str, Any] = {"message": str(exc)}
        mark = getattr(exc, "problem_mark", None)
        if mark is not None:
            details["line"] = mark.line + 1
            details["column"] = mark.column + 1
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "YAML 형식이 잘못되었습니다",
                "details": details,
            },
        )

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "YAML 루트는 객체(dict)여야 합니다",
            },
        )

    # 3. Resolve target path
    target = _resolve_scenario_file_path(scenario.file_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    # 4. Backup existing file (single .bak generation)
    backup_created = False
    if target.exists():
        bak = target.with_suffix(target.suffix + ".bak")
        try:
            shutil.copy2(target, bak)
            backup_created = True
        except OSError:
            # Backup failure should not block save; downgrade silently.
            backup_created = False

    # 5. Write
    try:
        target.write_text(payload.content, encoding="utf-8")
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write file: {exc}",
        )

    return ScenarioContentSaveResponse(
        id=scenario.id,
        file_path=scenario.file_path,
        size_bytes=len(payload.content.encode("utf-8")),
        saved_at=datetime.now(timezone.utc),
        backup_created=backup_created,
    )


# ============================================================================
# Test Execution (M9 — n8n YAML editor integration)
# ============================================================================


@router.post(
    "/{scenario_id}/test-runs",
    response_model=TestRunCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_test_run(
    db: DBSession,
    current_user: CurrentUser,
    scenario_id: int,
    payload: TestRunCreateRequest,
) -> TestRunCreateResponse:
    """Trigger an ad-hoc execution of the supplied workflow.

    The scenario id is validated to exist; the actual workflow JSON in the
    body is what gets executed (so the editor can run unsaved drafts).

    Design Ref: §4 POST /scenarios/{id}/test-runs
    Plan SC: #10 (Test Run -> 노드별 success/error 표시)
    """
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found",
        )

    state = await n8n_runner.start_execution(payload.workflow)
    return TestRunCreateResponse(
        execution_id=state.execution_id, status=state.status
    )


@router.get(
    "/test-runs/{execution_id}",
    response_model=TestRunStatusResponse,
)
async def get_test_run_status(
    current_user: CurrentUser,
    execution_id: str,
) -> TestRunStatusResponse:
    """Poll the per-node execution status."""
    state = n8n_runner.get_execution(execution_id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )
    payload = state.to_dict()
    return TestRunStatusResponse(
        execution_id=payload["execution_id"],
        status=payload["status"],
        started_at=state.started_at,
        finished_at=state.finished_at,
        nodes=payload["nodes"],
    )


@router.post(
    "/test-runs/{execution_id}/cancel",
    response_model=TestRunCancelResponse,
)
async def cancel_test_run(
    current_user: CurrentUser,
    execution_id: str,
) -> TestRunCancelResponse:
    """Request cancellation of a running execution."""
    state = await n8n_runner.cancel_execution(execution_id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )
    return TestRunCancelResponse(
        execution_id=state.execution_id, status=state.status
    )

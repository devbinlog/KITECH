from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse
import json
import yaml

from ....services.scenario_converter import (
    yaml_to_n8n_from_dict,
    n8n_to_yaml_from_dict,
    scenario_to_yaml_str
)
from ...deps import CurrentUser

router = APIRouter()

@router.post("/yaml-to-n8n", summary="YAML to n8n Converter")
async def convert_yaml_to_n8n(
    current_user: CurrentUser,
    file: UploadFile = File(..., description="The YAML scenario file to convert"),
    aas_path: str = Query("/data/cell1_aas.json", description="The AAS file path the n8n node should refer to inside the container"),
    base_url: str = Query("http://localhost:8080", description="The base URL parameter for the MES API"),
):
    """
    Converts a manufacturing YAML scenario file into an n8n workflow JSON structure.
    Returns the JSON payload directly so it can be downloaded recursively or pipelined to n8n API.
    """
    if not file.filename.endswith((".yaml", ".yml")):
        raise HTTPException(status_code=400, detail="Only YAML files are allowed.")

    content = await file.read()
    try:
        scenario_dict = yaml.safe_load(content.decode("utf-8"))
    except yaml.YAMLError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid YAML format: {exc}")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding must be UTF-8.")

    if not isinstance(scenario_dict, dict):
        raise HTTPException(status_code=400, detail="Root of YAML must be an object (dict)")

    try:
        workflow_json = yaml_to_n8n_from_dict(scenario_dict, aas_path=aas_path, base_url=base_url)
        return JSONResponse(content=workflow_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to convert YAML to n8n: {str(e)}")

@router.post("/n8n-to-yaml", summary="n8n to YAML Converter")
async def convert_n8n_to_yaml(
    current_user: CurrentUser,
    file: UploadFile = File(..., description="The n8n workflow JSON file to convert"),
):
    """
    Converts an n8n workflow JSON structure back into the standardized manufacturing YAML format.
    Returns the YAML content directly as plain text.
    """
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON files are allowed.")

    content = await file.read()
    try:
        workflow_dict = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {exc}")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding must be UTF-8.")

    try:
        scenario_dict = n8n_to_yaml_from_dict(workflow_dict)
        yaml_str = scenario_to_yaml_str(scenario_dict)
        return PlainTextResponse(content=yaml_str, media_type="application/x-yaml")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Validation error during conversion: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to convert n8n to YAML: {str(e)}")

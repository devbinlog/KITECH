import os
import re

iso_project_file = r"d:\과제\키테크\로봇\MES\agents-workspace_260323\Digital-Thread\ISO_api\src\apis\v3\project.py"
iso_asset_file = r"d:\과제\키테크\로봇\MES\agents-workspace_260323\Digital-Thread\ISO_api\src\apis\v3\asset.py"
output_service = r"src\services\cam_logic.py"

with open(iso_project_file, "r", encoding="utf-8") as f:
    proj_content = f.read()

# Extract imports
imports_match = re.search(r"^(.*?)(?=router = APIRouter)", proj_content, re.DOTALL)
imports = imports_match.group(1) if imports_match else ""

# Extract apply_cam_into_workplan
cam_match = re.search(r"async def apply_cam_into_workplan\((.*?)\) -> Dict\[str, Any\]:(.*?)(?=\n@router|\Z)", proj_content, re.DOTALL)
if cam_match:
    cam_sig = cam_match.group(1)
    cam_body = cam_match.group(2)
else:
    raise Exception("apply_cam_into_workplan not found")

# Modify signature and body for standard python
cam_body = cam_body.replace("await read_json_file(cam_files[0])", "json.load(open(cam_files[0], 'r', encoding='utf-8'))")
cam_body = cam_body.replace("await read_json_file(f)", "json.load(open(f, 'r', encoding='utf-8'))")
cam_body = cam_body.replace("await read_json_file(mapping_file)", "json.load(open(mapping_file, 'r', encoding='utf-8'))")
cam_body = cam_body.replace("f.filename", "os.path.basename(f)")
cam_body = cam_body.replace("cam_files[0].filename", "os.path.basename(cam_files[0])")

new_sig = """
    global_asset_id: str,
    asset_id: str,
    project_element_id: str,
    workplan_id: str,
    cam_type: str,
    cam_files: list[str],
    mapping_file: str,
    asset_service,
    file_service,
    project_service,
    ops_order: str = None
"""

new_cam_func = f"async def execute_apply_cam({new_sig}) -> dict:\n{cam_body}\n"

# Add standard json import
imports += "\nimport json\nimport os\n"

with open(output_service, "w", encoding="utf-8") as f:
    f.write(imports + "\n\n" + new_cam_func)

print("cam_logic.py generated successfully.")

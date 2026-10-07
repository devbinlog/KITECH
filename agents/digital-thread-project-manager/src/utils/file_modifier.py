import os
import shutil
import json
from datetime import datetime
from src.config import settings
import requests
from typing import Optional, Any
from fastapi import UploadFile


def zip_folder(source_dir: str, zip_path: str):
    """
    지정한 폴더(source_dir)를 zip_path로 압축 저장한다.
    zip_path는 .zip 확장자를 포함해야 한다.
    """
    base_name = os.path.splitext(zip_path)[0]
    shutil.make_archive(base_name, "zip", root_dir=source_dir)
    return zip_path


def create_prj_file(
    stock_type: int,
    stock_coords: list[float],
    nc_file_paths: list[str],
    tool_infos: list[list],
    output_path: str,
):
    """
    NC 파일 경로들과 툴 정보, 프로젝트의 소재 정보를 이용하여 .prj 파일 생성
    """

    stock_size = ",".join(
        [str(int(x)) if x.is_integer() else str(x) for x in stock_coords]
    )

    # 3. 툴 정보 → 문자열 변환
    def format_tool_data(t: list) -> str:
        return ",".join(
            [str(t[0])]
            + [
                f"{float(x):.6f}" if isinstance(x, (float, int)) else str(x)
                for x in t[1:]
            ]
        )

    # 4. process 목록 생성
    process_list = []
    for nc_path, tool in zip(nc_file_paths, tool_infos):
        # 경로 처리
        nc_path_norm = nc_path.replace("/", "\\")
        ncdata_idx = nc_path_norm.lower().find("ncdata\\")
        if ncdata_idx != -1:
            relative_path = nc_path_norm[ncdata_idx:]
        else:
            relative_path = nc_path_norm

        # 파일명 스템 추출 (예: Test_Project1_2)
        file_stem = os.path.splitext(os.path.basename(nc_path))[0]

        # 원하는 출력 경로 구성
        output_dir_path = os.path.join("result", file_stem).replace("/", "\\")

        process_list.append(
            {
                "file_path": relative_path.replace(".nc", ""),
                "output_dir_path": output_dir_path,
                "tool_data": format_tool_data(tool),
            }
        )

    # 5. 최종 .prj 구조
    prj_data = {
        "stock_type": stock_type,
        "stock_size": stock_size,
        "process_count": len(process_list),
        "process": process_list,
    }

    # 6. 저장
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(prj_data, f, indent=2)

    return output_path


def create_vm_project_name() -> str:
    """
    현재 시간을 기반으로 프로젝트 명을 생성 (예: 2025-07-01_ap_10_23_45)
    """
    now = datetime.now()

    year = now.year
    month = f"{now.month:02d}"
    day = f"{now.day:02d}"
    hour_24 = now.hour
    minute = f"{now.minute:02d}"
    second = f"{now.second:02d}"

    ampm = "pp" if hour_24 >= 12 else "ap"
    hour_12 = hour_24 % 12 or 12

    return f"{year}-{month}-{day}_{ampm}_{hour_12}_{minute}_{second}"


def vm_file_s3_upload(file_path: str, parent_path: Optional[str] = None):
    """
    생성한 프로젝트 파일과 ncdata.zip 파일을 s3에 업로드 하는 함수.
    """

    """
    S3 업로드 API 호출 함수 (TypeScript postMacsimUpload 대응)
    
    :param parent_path: S3 업로드 대상 상위 경로
    :param file_path: 업로드할 로컬 파일 경로
    :param s3_url: 업로드용 API 엔드포인트 (예: http://your-host/s3-upload)
    :return: 응답 JSON 또는 에러 dict
    """
    s3_url = f"{settings.vm_api_url}/s3-upload"

    params = {}
    if parent_path:
        params["parent_path"] = parent_path

    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(s3_url, params=params, files=files)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}


async def read_json_file(f: UploadFile) -> Any:
    raw = await f.read()
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return json.loads(raw)  # 혹시 이미 str이면

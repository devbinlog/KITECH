"""
DTP REST API 통합 테스트

테스트 로직과 데이터 설정을 완전히 분리한다.
테스트 시나리오(DTPTestScenario)만 교체하면 어떤 샘플 데이터로도 동일한 테스트를 실행할 수 있다.

── 실행 방법 ──────────────────────────────────────────────────────────────────
  # 기본 (iso301_sample 시나리오, 로컬 서버)
  pytest tests/test_integration_api.py -m integration -v -s

  # Docker 환경 (서버 측 샘플 경로 지정)
  DTP_SERVER_SAMPLES_DIR=/app/samples \\
  pytest tests/test_integration_api.py -m integration -v -s

── 환경변수 ───────────────────────────────────────────────────────────────────
  DTP_BASE_URL            DTP 서버 URL               (default: http://localhost:8205)
  DTP_MONGO_URI           MongoDB URI                (default: mongodb://localhost:28017)
  DTP_DB_NAME             DB 이름                    (default: iso14649)
  DTP_SAMPLES_DIR         클라이언트 측 샘플 루트     (default: <workspace>/samples/digital-thread-project-manager)
  DTP_SERVER_SAMPLES_DIR  서버 측 샘플 루트           (default: DTP_SAMPLES_DIR 동일)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pytest
import requests

# ── 서버 / DB 접속 정보 ────────────────────────────────────────────────────────
BASE_URL  = os.environ.get("DTP_BASE_URL",  "http://localhost:8205")
MONGO_URI = os.environ.get("DTP_MONGO_URI", "mongodb://localhost:28017")
DB_NAME   = os.environ.get("DTP_DB_NAME",  "iso14649")

_default_samples = Path(__file__).parent.parent.parent.parent / "samples" / "digital-thread-project-manager"
CLIENT_SAMPLES_DIR = Path(os.environ.get("DTP_SAMPLES_DIR", str(_default_samples)))
SERVER_SAMPLES_DIR = Path(os.environ.get("DTP_SERVER_SAMPLES_DIR", str(CLIENT_SAMPLES_DIR)))


# ── 테스트 시나리오 정의 ──────────────────────────────────────────────────────
@dataclass
class DTPTestScenario:
    """한 번의 통합 테스트 실행에 필요한 모든 설정.

    테스트 로직은 이 객체만 참조한다.
    다른 샘플로 테스트하려면 새 DTPTestScenario 인스턴스를 만들어
    scenario() 픽스처에서 반환하면 된다.
    """

    # 식별자 — XML 파일 안의 값과 일치해야 함
    global_asset_id: str
    project_asset_id: str
    project_element_id: str
    workplan_id: str
    material_asset_id: str
    material_element_id: str
    machine_asset_id: str
    machine_element_id: str

    # 클라이언트 측 경로 — XML 내용을 읽어 api에 문자열로 전송
    project_xml: Path
    material_xml: Path
    machine_tool_xml: Path

    # 서버 측 경로 — DTP 서버 프로세스가 직접 open()하는 경로
    nc_file: str           # upload_nc_file
    cam_type: str          # "powermill" | "nx"
    cam_files: list[str]   # apply_cam_json cam_files
    mapping_file: str      # apply_cam_json mapping_file
    ops_order: str         # apply_cam_json ops_order (powermill 필수, nx는 빈 문자열 가능)

    # 선택적 첨부 파일 (없으면 해당 테스트 자동 skip)
    thumbnail_file: Optional[str] = None
    step_file: Optional[str] = None


# ── iso301_sample 시나리오 ────────────────────────────────────────────────────
_C = CLIENT_SAMPLES_DIR / "iso301_sample"   # 클라이언트 측 루트
_S = str(SERVER_SAMPLES_DIR / "iso301_sample")  # 서버 측 루트

ISO301_SCENARIO = DTPTestScenario(
    # 식별자 (xml 파일과 일치)
    global_asset_id    = "https://digital-thread.re/kitech/dtp_test",
    project_asset_id   = "dtp_test_project",
    project_element_id = "dtp_test_project_elem",
    workplan_id        = "dtp_test_wp_001",
    material_asset_id  = "dtp_test_material",
    material_element_id= "dtp_test_material_elem",
    machine_asset_id   = "dtp_test_machine",
    machine_element_id = "dtp_test_machine_elem",

    # 클라이언트 측 XML
    project_xml     = _C / "xml/project_sample.xml",
    material_xml    = _C / "xml/kimm_material.xml",
    machine_tool_xml= _C / "xml/kimm_machine_tool.xml",

    # 서버 측 파일
    nc_file      = f"{_S}/301_op1.tap",
    cam_type     = "powermill",
    cam_files    = [
        f"{_S}/json/first/face1.json",
        f"{_S}/json/first/2D_pocket4.json",
        f"{_S}/json/first/2D_contour3.json",
        f"{_S}/json/first/2D_contour4.json",
        f"{_S}/json/first/drill4.json",
        f"{_S}/json/first/2D_pocket2.json",
        f"{_S}/json/first/2D_pocket7.json",
        f"{_S}/json/first/2D_pocket6.json",
    ],
    mapping_file = f"{_S}/json/mapping_config_constantz.json",
    ops_order    = (_C / "json/first/workingstep_order.txt").read_text(encoding="utf-8").strip(),

    thumbnail_file = f"{_S}/301_thumbnail.png",
    step_file      = f"{_S}/301.step",
)


# ── 픽스처 ────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def scenario() -> DTPTestScenario:
    """실행할 테스트 시나리오. 다른 샘플로 교체하려면 여기만 수정한다."""
    return ISO301_SCENARIO


@pytest.fixture(scope="module")
def mongo_db():
    """pymongo 직접 연결 — DB 상태 검증용. 연결 불가 시 None."""
    try:
        from pymongo import MongoClient
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        client.server_info()
        db = client[DB_NAME]
        yield db
        client.close()
    except Exception as exc:
        print(f"\n[WARN] MongoDB 직접 연결 실패 — DB 검증 건너뜀: {exc}")
        yield None


@pytest.fixture(scope="module", autouse=True)
def cleanup(scenario: DTPTestScenario, mongo_db):
    """테스트 전 해당 시나리오 데이터 정리."""
    if mongo_db is not None:
        mongo_db["assets"].delete_many({"global_asset_id": scenario.global_asset_id})
    yield
    # 테스트 후 데이터를 남겨두면 MongoDB Compass로 결과 확인 가능.
    # 자동 정리를 원하면 아래 주석 해제:
    # if mongo_db is not None:
    #     mongo_db["assets"].delete_many({"global_asset_id": scenario.global_asset_id})


# ── 테스트 클래스 ──────────────────────────────────────────────────────────────
@pytest.mark.integration
class TestDTPIntegration:
    """API 의존성 순서에 따른 end-to-end 통합 테스트.

    모든 테스트는 scenario 픽스처만 참조한다.
    테스트 로직은 데이터와 완전히 분리되어 있다.
    """

    # ── [사전 확인] ────────────────────────────────────────────────────────────

    def test_00_server_reachable(self):
        try:
            requests.get(f"{BASE_URL}/health", timeout=5)
        except requests.ConnectionError:
            pytest.fail(
                f"DTP 서버에 연결할 수 없음: {BASE_URL}\n"
                f"  로컬: uvicorn src.server:app --port 8205\n"
                f"  Docker: docker compose -f agents/digital-thread-project-manager/docker-compose.yml up -d"
            )

    def test_00b_scenario_files_exist(self, scenario: DTPTestScenario):
        """시나리오에 정의된 클라이언트 측 파일이 모두 존재하는지 확인."""
        required = [
            scenario.project_xml,
            scenario.material_xml,
            scenario.machine_tool_xml,
        ]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            pytest.fail("시나리오 파일 없음:\n" + "\n".join(missing))

    # ── [Meta] ─────────────────────────────────────────────────────────────────

    def test_01_health(self):
        r = requests.get(f"{BASE_URL}/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        assert r.json()["service"] == "dtp"

    def test_02_capabilities(self):
        r = requests.get(f"{BASE_URL}/capabilities")
        assert r.status_code == 200
        tool_names = {t["name"] for t in r.json()["tools"]}
        expected = {
            "get_projects", "create_project", "create_asset",
            "upload_nc_file", "apply_cam_json", "attach_project_ref",
            "upload_and_attach_file", "upload_project_to_dp",
        }
        assert expected == tool_names

    # ── [프로젝트 생성] ────────────────────────────────────────────────────────

    def test_03_create_project(self, scenario: DTPTestScenario, mongo_db):
        xml = scenario.project_xml.read_text(encoding="utf-8")
        r = requests.post(f"{BASE_URL}/tools/create_project", params={"xml_string": xml})
        assert r.status_code == 200, f"create_project 실패: {r.text}"

        if mongo_db is not None:
            doc = mongo_db["assets"].find_one({
                "global_asset_id": scenario.global_asset_id,
                "asset_id": scenario.project_asset_id,
                "type": "dt_project",
            })
            assert doc is not None, "dt_project 문서가 DB에 없음"
            assert doc["element_id"] == scenario.project_element_id

    def test_04_get_projects(self, scenario: DTPTestScenario):
        r = requests.get(f"{BASE_URL}/tools/get_projects")
        assert r.status_code == 200
        asset_ids = [p.get("asset_id") for p in r.json()["projects"]]
        assert scenario.project_asset_id in asset_ids, (
            f"get_projects에 '{scenario.project_asset_id}' 없음: {asset_ids}"
        )

    def test_05_create_project_duplicate_returns_409(self, scenario: DTPTestScenario, mongo_db):
        """동일 키로 두 번째 create_project → 409 Conflict 확인."""
        xml = scenario.project_xml.read_text(encoding="utf-8")
        r = requests.post(f"{BASE_URL}/tools/create_project", params={"xml_string": xml})
        assert r.status_code == 409, (
            f"중복 create_project가 409를 반환하지 않음: {r.status_code} {r.text}"
        )

        if mongo_db is not None:
            count = mongo_db["assets"].count_documents({
                "global_asset_id": scenario.global_asset_id,
                "asset_id": scenario.project_asset_id,
                "type": "dt_project",
            })
            assert count == 1, f"중복 문서 생성됨 (count={count})"

    # ── [NC 파일 등록] ─────────────────────────────────────────────────────────

    def test_06_upload_nc_file(self, scenario: DTPTestScenario, mongo_db):
        params = {
            "global_asset_id": scenario.global_asset_id,
            "asset_id":        scenario.project_asset_id,
            "element_id":      scenario.project_element_id,
            "workplan_id":     scenario.workplan_id,
            "nc_file_path":    scenario.nc_file,
        }
        r = requests.post(f"{BASE_URL}/tools/upload_nc_file", params=params)
        assert r.status_code == 200, (
            f"upload_nc_file 실패: {r.status_code} {r.text}\n"
            f"  nc_file={scenario.nc_file}\n"
            f"  (Docker 사용 시 DTP_SERVER_SAMPLES_DIR 환경변수 확인)"
        )

        if mongo_db is not None:
            nc_docs = list(mongo_db["assets"].find({
                "global_asset_id": scenario.global_asset_id,
                "type": "dt_file",
                "category": "NC",
            }))
            assert len(nc_docs) >= 1, "dt_file(NC) 문서가 DB에 없음"

    def test_07_upload_nc_file_duplicate_blocked(self, scenario: DTPTestScenario):
        params = {
            "global_asset_id": scenario.global_asset_id,
            "asset_id":        scenario.project_asset_id,
            "element_id":      scenario.project_element_id,
            "workplan_id":     scenario.workplan_id,
            "nc_file_path":    scenario.nc_file,
        }
        r = requests.post(f"{BASE_URL}/tools/upload_nc_file", params=params)
        assert r.status_code in (400, 409), (
            f"NC 중복 업로드가 오류를 반환하지 않음: {r.status_code} {r.text}"
        )

    # ── [CAM JSON 적용] ────────────────────────────────────────────────────────

    def test_08_apply_cam_without_nc_fails(self, scenario: DTPTestScenario):
        """NC 없는 별도 프로젝트에 apply → 404 확인."""
        tmp_asset_id = f"{scenario.project_asset_id}_no_nc_tmp"
        tmp_element_id = f"{scenario.project_element_id}_no_nc"
        tmp_wp_id = f"{scenario.workplan_id}_no_nc"

        # 임시 프로젝트 생성 (NC 없음)
        xml = scenario.project_xml.read_text(encoding="utf-8")
        xml = (xml
               .replace(scenario.project_asset_id, tmp_asset_id)
               .replace(scenario.project_element_id, tmp_element_id)
               .replace(scenario.workplan_id, tmp_wp_id))
        requests.post(f"{BASE_URL}/tools/create_project", params={"xml_string": xml})

        payload = {
            "global_asset_id":    scenario.global_asset_id,
            "asset_id":           tmp_asset_id,
            "project_element_id": tmp_element_id,
            "workplan_id":        tmp_wp_id,
            "cam_type":           scenario.cam_type,
            "cam_files":          [scenario.cam_files[0]],
            "mapping_file":       scenario.mapping_file,
            "ops_order":          scenario.cam_files[0].split("/")[-1],
        }
        r = requests.post(f"{BASE_URL}/tools/apply_cam_json", json=payload)
        assert r.status_code == 404, (
            f"NC 없는 프로젝트에 apply_cam_json이 404를 반환하지 않음: "
            f"{r.status_code} {r.text}"
        )

    def test_09_apply_cam_json(self, scenario: DTPTestScenario, mongo_db):
        payload = {
            "global_asset_id":    scenario.global_asset_id,
            "asset_id":           scenario.project_asset_id,
            "project_element_id": scenario.project_element_id,
            "workplan_id":        scenario.workplan_id,
            "cam_type":           scenario.cam_type,
            "cam_files":          scenario.cam_files,
            "mapping_file":       scenario.mapping_file,
            "ops_order":          scenario.ops_order,
        }
        r = requests.post(f"{BASE_URL}/tools/apply_cam_json", json=payload)
        assert r.status_code == 200, (
            f"apply_cam_json 실패: {r.status_code} {r.text}"
        )

        if mongo_db is not None:
            tools = list(mongo_db["assets"].find({
                "global_asset_id": scenario.global_asset_id,
                "type": "dt_cutting_tool_13399",
            }))
            assert len(tools) > 0, "dt_cutting_tool_13399 문서가 생성되지 않음"

            prj_doc = mongo_db["assets"].find_one({
                "asset_id": scenario.project_asset_id,
                "type": "dt_project",
            })
            data = prj_doc["data"].lower()
            assert "machining_workingstep" in data or "its_elements" in data, (
                "프로젝트 XML에 워킹스텝이 추가되지 않음"
            )

    def test_10_apply_cam_json_already_has_workingsteps(self, scenario: DTPTestScenario):
        """워킹스텝이 이미 있는 프로젝트에 재실행 → 400/409."""
        payload = {
            "global_asset_id":    scenario.global_asset_id,
            "asset_id":           scenario.project_asset_id,
            "project_element_id": scenario.project_element_id,
            "workplan_id":        scenario.workplan_id,
            "cam_type":           scenario.cam_type,
            "cam_files":          scenario.cam_files,
            "mapping_file":       scenario.mapping_file,
            "ops_order":          scenario.ops_order,
        }
        r = requests.post(f"{BASE_URL}/tools/apply_cam_json", json=payload)
        assert r.status_code in (400, 409), (
            f"중복 apply_cam_json이 오류를 반환하지 않음: {r.status_code} {r.text}"
        )

    # ── [참조 연결] ────────────────────────────────────────────────────────────

    def test_11_create_material(self, scenario: DTPTestScenario, mongo_db):
        xml = scenario.material_xml.read_text(encoding="utf-8")
        r = requests.post(f"{BASE_URL}/tools/create_asset", params={"xml_string": xml})
        assert r.status_code == 200, f"material 등록 실패: {r.text}"

        if mongo_db is not None:
            doc = mongo_db["assets"].find_one({
                "global_asset_id": scenario.global_asset_id,
                "asset_id": scenario.material_asset_id,
                "type": "dt_material",
            })
            assert doc is not None, "dt_material 문서가 DB에 없음"

    def test_12_attach_material_ref(self, scenario: DTPTestScenario):
        params = {
            "global_asset_id":    scenario.global_asset_id,
            "asset_id":           scenario.project_asset_id,
            "project_element_id": scenario.project_element_id,
            "ref_global_asset_id": scenario.global_asset_id,
            "ref_asset_id":       scenario.material_asset_id,
            "ref_element_id":     scenario.material_element_id,
            "ref_type":           "dt_material",
            "workplan_id":        scenario.workplan_id,
        }
        r = requests.post(f"{BASE_URL}/tools/attach_project_ref", params=params)
        assert r.status_code == 200, f"attach_project_ref(dt_material) 실패: {r.text}"

    def test_13_create_machine_tool(self, scenario: DTPTestScenario, mongo_db):
        xml = scenario.machine_tool_xml.read_text(encoding="utf-8")
        r = requests.post(f"{BASE_URL}/tools/create_asset", params={"xml_string": xml})
        assert r.status_code == 200, f"machine_tool 등록 실패: {r.text}"

        if mongo_db is not None:
            doc = mongo_db["assets"].find_one({
                "global_asset_id": scenario.global_asset_id,
                "asset_id": scenario.machine_asset_id,
                "type": "dt_machine_tool",
            })
            assert doc is not None, "dt_machine_tool 문서가 DB에 없음"

    def test_14_attach_machine_tool_ref(self, scenario: DTPTestScenario):
        params = {
            "global_asset_id":    scenario.global_asset_id,
            "asset_id":           scenario.project_asset_id,
            "project_element_id": scenario.project_element_id,
            "ref_global_asset_id": scenario.global_asset_id,
            "ref_asset_id":       scenario.machine_asset_id,
            "ref_element_id":     scenario.machine_element_id,
            "ref_type":           "dt_machine_tool",
            "workplan_id":        scenario.workplan_id,
        }
        r = requests.post(f"{BASE_URL}/tools/attach_project_ref", params=params)
        assert r.status_code == 200, f"attach_project_ref(dt_machine_tool) 실패: {r.text}"

    # ── [파일 첨부] ────────────────────────────────────────────────────────────

    def test_15_upload_thumbnail(self, scenario: DTPTestScenario):
        if not scenario.thumbnail_file:
            pytest.skip("시나리오에 thumbnail_file 미설정")
        payload = {
            "global_asset_id":    scenario.global_asset_id,
            "asset_id":           scenario.project_asset_id,
            "project_element_id": scenario.project_element_id,
            "workplan_id":        scenario.workplan_id,
            "file_path":          scenario.thumbnail_file,
            "ref_type":           "dt_file",
            "ref_category":       "TITLE_IMAGE",
        }
        r = requests.post(f"{BASE_URL}/tools/upload_and_attach_file", json=payload)
        assert r.status_code == 200, f"thumbnail 업로드 실패: {r.status_code} {r.text}"

    def test_16_upload_step(self, scenario: DTPTestScenario):
        if not scenario.step_file:
            pytest.skip("시나리오에 step_file 미설정")
        payload = {
            "global_asset_id":    scenario.global_asset_id,
            "asset_id":           scenario.project_asset_id,
            "project_element_id": scenario.project_element_id,
            "workplan_id":        scenario.workplan_id,
            "file_path":          scenario.step_file,
            "ref_type":           "dt_file",
            "ref_category":       "STEP",
        }
        r = requests.post(f"{BASE_URL}/tools/upload_and_attach_file", json=payload)
        assert r.status_code == 200, f"STEP 업로드 실패: {r.status_code} {r.text}"

    # ── [최종 상태 검증] ───────────────────────────────────────────────────────

    def test_17_final_state(self, scenario: DTPTestScenario, mongo_db):
        if mongo_db is None:
            pytest.skip("MongoDB 연결 없음")

        gid = scenario.global_asset_id

        prj_id = scenario.project_asset_id
        counts = {
            "dt_project":            mongo_db["assets"].count_documents({"global_asset_id": gid, "asset_id": prj_id, "type": "dt_project"}),
            "dt_file(NC)":           mongo_db["assets"].count_documents({"global_asset_id": gid, "type": "dt_file", "category": "NC"}),
            "dt_cutting_tool_13399": mongo_db["assets"].count_documents({"global_asset_id": gid, "type": "dt_cutting_tool_13399"}),
            "dt_material":           mongo_db["assets"].count_documents({"global_asset_id": gid, "type": "dt_material"}),
            "dt_machine_tool":       mongo_db["assets"].count_documents({"global_asset_id": gid, "type": "dt_machine_tool"}),
        }

        print("\n[최종 DB 상태]")
        for k, v in counts.items():
            print(f"  {k:30s}: {v}")

        assert counts["dt_project"]            == 1, "dt_project 없음"
        assert counts["dt_file(NC)"]           >= 1, "dt_file(NC) 없음"
        assert counts["dt_cutting_tool_13399"] >  0, "dt_cutting_tool_13399 없음"
        assert counts["dt_material"]           == 1, "dt_material 없음"
        assert counts["dt_machine_tool"]       == 1, "dt_machine_tool 없음"

    # ── [DP 업로드 — 실 연결 필요] ────────────────────────────────────────────

    @pytest.mark.skipif(
        not os.environ.get("DTP_TEST_DP_UPLOAD"),
        reason="DTP_TEST_DP_UPLOAD=1 환경변수 설정 시에만 실행"
    )
    def test_18_upload_to_dp(self, scenario: DTPTestScenario):
        params = {
            "global_asset_id":    scenario.global_asset_id,
            "asset_id":           scenario.project_asset_id,
            "project_element_id": scenario.project_element_id,
        }
        r = requests.post(f"{BASE_URL}/tools/upload_project_to_dp", params=params)
        assert r.status_code == 200, f"upload_project_to_dp 실패: {r.text}"

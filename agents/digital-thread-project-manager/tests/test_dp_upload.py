"""
DP 업로드 단독 테스트

통합 테스트(test_integration_api.py)로 생성된 데이터가 MongoDB에 남아있는 상태에서
POST /tools/upload_project_to_dp 만 검증한다.

DB cleanup 없음 — 기존 데이터를 그대로 사용한다.

── 실행 방법 ──────────────────────────────────────────────────────────────────
  DTP_BASE_URL=http://localhost:8205 \\
  DTP_MONGO_URI=mongodb://localhost:28017 \\
  pytest tests/test_dp_upload.py -v -s
"""

import os

import pytest
import requests
from pymongo import MongoClient

BASE_URL  = os.environ.get("DTP_BASE_URL",  "http://localhost:8205")
MONGO_URI = os.environ.get("DTP_MONGO_URI", "mongodb://localhost:28017")
DB_NAME   = os.environ.get("DTP_DB_NAME",   "iso14649")

GLOBAL_ASSET_ID    = "https://digital-thread.re/kitech/dtp_test"
PROJECT_ASSET_ID   = "dtp_test_project"
PROJECT_ELEMENT_ID = "dtp_test_project_elem"


@pytest.fixture(scope="module")
def mongo_db():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    db = client[DB_NAME]
    yield db
    client.close()


class TestDPUpload:

    def test_00_server_reachable(self):
        try:
            r = requests.get(f"{BASE_URL}/health", timeout=5)
            assert r.status_code == 200
        except requests.ConnectionError:
            pytest.fail(f"DTP 서버에 연결할 수 없음: {BASE_URL}")

    def test_01_data_exists_in_db(self, mongo_db):
        """업로드 전 필수 데이터가 DB에 있는지 확인."""
        col = mongo_db["assets"]
        project = col.find_one({
            "global_asset_id": GLOBAL_ASSET_ID,
            "asset_id": PROJECT_ASSET_ID,
            "type": "dt_project",
        })
        assert project is not None, (
            "dt_project 데이터 없음 — test_integration_api.py를 먼저 실행해 데이터를 생성하세요."
        )

        counts = {
            t: col.count_documents({"global_asset_id": GLOBAL_ASSET_ID, "type": t})
            for t in ["dt_project", "dt_file", "dt_cutting_tool_13399", "dt_material", "dt_machine_tool"]
        }
        print("\n[DB 현황]")
        for t, c in counts.items():
            print(f"  {t}: {c}")

        assert counts["dt_project"]            >= 1, "dt_project 없음"
        assert counts["dt_file"]               >= 1, "dt_file(NC) 없음"
        assert counts["dt_cutting_tool_13399"] >= 1, "dt_cutting_tool_13399 없음"

    def test_02_upload_project_to_dp(self, mongo_db):
        """POST /tools/upload_project_to_dp — 실 DP 서버에 업로드."""
        r = requests.post(
            f"{BASE_URL}/tools/upload_project_to_dp",
            params={
                "global_asset_id":    GLOBAL_ASSET_ID,
                "asset_id":           PROJECT_ASSET_ID,
                "project_element_id": PROJECT_ELEMENT_ID,
            },
            timeout=60,
        )
        print(f"\n[응답] status={r.status_code}")
        print(r.text[:2000])
        assert r.status_code == 200, f"upload_project_to_dp 실패: {r.text}"

    def test_03_is_upload_flag_set(self, mongo_db):
        """업로드 후 dt_project 문서의 is_upload 플래그가 True인지 확인."""
        doc = mongo_db["assets"].find_one({
            "global_asset_id": GLOBAL_ASSET_ID,
            "asset_id": PROJECT_ASSET_ID,
            "type": "dt_project",
        })
        assert doc is not None
        assert doc.get("is_upload") is True, (
            f"is_upload 플래그가 True가 아님: {doc.get('is_upload')}"
        )

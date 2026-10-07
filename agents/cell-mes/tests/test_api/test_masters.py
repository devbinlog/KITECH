"""Tests for master data endpoints (Products, StdProcesses)."""

import pytest
from httpx import AsyncClient

from src.app.models.master import ProcessRoutingFile, Product


class TestMasterFileContent:
    """Test master file content endpoints."""

    @pytest.mark.asyncio
    async def test_nc_file_download_returns_inline_text(
        self, client: AsyncClient, auth_headers, sample_routing, db_session, tmp_path, monkeypatch
    ):
        """NC file endpoint returns raw text content instead of attachment download."""
        monkeypatch.chdir(tmp_path)
        upload_dir = tmp_path / "uploads" / "nc"
        upload_dir.mkdir(parents=True)
        nc_file = upload_dir / "test.nc"
        nc_file.write_text("G00 X0 Y0\nM30\n", encoding="utf-8")

        routing_file = ProcessRoutingFile(
            process_routing_id=sample_routing.id,
            file_type="NC",
            file_path="/uploads/nc/test.nc",
            original_filename="original.nc",
            sort_order=1,
        )
        db_session.add(routing_file)
        await db_session.commit()
        await db_session.refresh(routing_file)

        response = await client.get(
            f"/api/v1/masters/files/{routing_file.id}/download",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert "content-disposition" not in response.headers
        assert response.text == "G00 X0 Y0\nM30\n"

    @pytest.mark.asyncio
    async def test_nc_file_download_returns_404_when_db_path_file_is_missing(
        self, client: AsyncClient, auth_headers, sample_routing, db_session, tmp_path, monkeypatch
    ):
        """Missing DB file path returns 404 even if a same-named legacy data file exists."""
        monkeypatch.chdir(tmp_path)
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        nc_file = data_dir / "O0010"
        nc_file.write_text("%\nO0010\nM30\n%\n", encoding="utf-8")

        routing_file = ProcessRoutingFile(
            process_routing_id=sample_routing.id,
            file_type="NC",
            file_path="/uploads/nc/missing-upload-id",
            original_filename="O0010",
            sort_order=1,
        )
        db_session.add(routing_file)
        await db_session.commit()
        await db_session.refresh(routing_file)

        response = await client.get(
            f"/api/v1/masters/files/{routing_file.id}/download",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "File not found on disk"


class TestStdProcessList:
    """Test standard process list endpoint."""

    @pytest.mark.asyncio
    async def test_list_std_processes_empty(self, client: AsyncClient, auth_headers):
        """List returns empty when no processes exist."""
        response = await client.get("/api/v1/masters/std-processes", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_std_processes(self, client: AsyncClient, auth_headers, sample_std_process):
        """List returns all standard processes."""
        response = await client.get("/api/v1/masters/std-processes", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["code"] == "STD-CUT-01"
        assert data[0]["name"] == "레이저 절단"

    @pytest.mark.asyncio
    async def test_list_std_processes_unauthorized(self, client: AsyncClient):
        """Unauthorized request returns 401."""
        response = await client.get("/api/v1/masters/std-processes")

        assert response.status_code == 401


class TestStdProcessCreate:
    """Test standard process creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_std_process(self, client: AsyncClient, auth_headers):
        """Create a new standard process."""
        response = await client.post(
            "/api/v1/masters/std-processes",
            headers=auth_headers,
            json={
                "code": "STD-WELD-01",
                "name": "용접 공정",
                "description": "아크 용접 공정입니다.",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "STD-WELD-01"
        assert data["name"] == "용접 공정"
        assert data["description"] == "아크 용접 공정입니다."
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_std_process_duplicate_code(
        self, client: AsyncClient, auth_headers, sample_std_process
    ):
        """Duplicate code returns 400."""
        response = await client.post(
            "/api/v1/masters/std-processes",
            headers=auth_headers,
            json={
                "code": "STD-CUT-01",  # Same as sample_std_process
                "name": "다른 절단",
            },
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_std_process_missing_required(self, client: AsyncClient, auth_headers):
        """Missing required fields returns 422."""
        response = await client.post(
            "/api/v1/masters/std-processes",
            headers=auth_headers,
            json={"description": "Only description"},  # Missing code and name
        )

        assert response.status_code == 422


class TestStdProcessGet:
    """Test standard process get endpoint."""

    @pytest.mark.asyncio
    async def test_get_std_process(self, client: AsyncClient, auth_headers, sample_std_process):
        """Get a standard process by ID."""
        response = await client.get(
            f"/api/v1/masters/std-processes/{sample_std_process.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_std_process.id
        assert data["code"] == "STD-CUT-01"

    @pytest.mark.asyncio
    async def test_get_std_process_not_found(self, client: AsyncClient, auth_headers):
        """Non-existent process returns 404."""
        response = await client.get(
            "/api/v1/masters/std-processes/9999",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestProductList:
    """Test product list endpoint."""

    @pytest.mark.asyncio
    async def test_list_products_empty(self, client: AsyncClient, auth_headers):
        """List returns empty when no products exist."""
        response = await client.get("/api/v1/masters/products", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_products(self, client: AsyncClient, auth_headers, sample_product):
        """List returns all products."""
        response = await client.get("/api/v1/masters/products", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["code"] == "PROD-001"
        assert data[0]["name"] == "테스트 제품"

    @pytest.mark.asyncio
    async def test_list_products_excludes_deleted(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """List excludes soft-deleted products by default."""
        # Create a deleted product
        deleted_product = Product(
            code="PROD-DEL",
            name="삭제된 제품",
            is_deleted=True,
        )
        db_session.add(deleted_product)
        await db_session.commit()

        response = await client.get("/api/v1/masters/products", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        # Only sample_product should be returned
        assert len(data) == 1
        assert data[0]["code"] == "PROD-001"

    @pytest.mark.asyncio
    async def test_list_products_include_deleted(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """List includes deleted products when requested."""
        # Create a deleted product
        deleted_product = Product(
            code="PROD-DEL",
            name="삭제된 제품",
            is_deleted=True,
        )
        db_session.add(deleted_product)
        await db_session.commit()

        response = await client.get(
            "/api/v1/masters/products?include_deleted=true",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestProductCreate:
    """Test product creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_product(self, client: AsyncClient, auth_headers):
        """Create a new product."""
        response = await client.post(
            "/api/v1/masters/products",
            headers=auth_headers,
            json={
                "code": "PROD-NEW",
                "name": "신규 제품",
                "unit": "SET",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "PROD-NEW"
        assert data["name"] == "신규 제품"
        assert data["unit"] == "SET"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_product_default_unit(self, client: AsyncClient, auth_headers):
        """Product uses default unit 'EA' when not specified."""
        response = await client.post(
            "/api/v1/masters/products",
            headers=auth_headers,
            json={
                "code": "PROD-DEFAULT",
                "name": "기본 단위 제품",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["unit"] == "EA"

    @pytest.mark.asyncio
    async def test_create_product_without_dt_project_allows_parentheses(
        self, client: AsyncClient, auth_headers
    ):
        """DT Project is optional and product names may include cell suffixes."""
        response = await client.post(
            "/api/v1/masters/products",
            headers=auth_headers,
            json={
                "code": "PLAT-A002",
                "name": "드릴 지그 플레이트(cell1)",
                "unit": "EA",
                "dt_project": None,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "드릴 지그 플레이트(cell1)"
        assert data["current_dt_project"] is None

    @pytest.mark.asyncio
    async def test_create_product_with_dt_project_and_list_workplan_nc(
        self, client: AsyncClient, auth_headers, monkeypatch
    ):
        """DT Project can be linked optionally and NC files are filtered by workplan refs."""
        async def fake_get_project_tree(self, asset_global_id, asset_id):
            return {
                "id": 370,
                "xmlStr": """
                <project xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                  <main_workplan>
                    <its_id>mainworkplan</its_id>
                    <its_elements xsi:type="workplan">
                      <its_id>wp_001</its_id>
                    </its_elements>
                  </main_workplan>
                </project>
                """,
            }

        async def fake_find_nc_files(self, asset_global_id):
            return [
                {
                    "id": "nc_001",
                    "elementId": "merge.tap",
                    "category": "NC",
                    "path": "/userdata/3/merge.tap",
                    "reflist": [
                        {
                            "keys": [
                                {
                                    "key": "DT_GLOBAL_ASSET",
                                    "value": "https://digital-thread.re/kitech/kimm_project",
                                },
                                {"key": "DT_ASSET", "value": "prj_001"},
                                {"key": "DT_PROJECT", "value": "milling_prj"},
                                {"key": "WORKPLAN", "value": "wp_001"},
                            ]
                        }
                    ],
                },
                {
                    "id": "nc_other",
                    "elementId": "other.tap",
                    "category": "NC",
                    "path": "/userdata/3/other.tap",
                    "references": {
                        "DT_global_asset": "https://digital-thread.re/kitech/kimm_project",
                        "DT_asset": "https://digital-thread.re/kitech/kimm_project/prj_002",
                        "DT_project": "other_prj",
                        "DT_project_workplan": "wp_001",
                    },
                },
            ]

        monkeypatch.setattr(
            "src.app.api.v1.endpoints.masters.DtpClient.get_project_tree",
            fake_get_project_tree,
        )
        monkeypatch.setattr(
            "src.app.api.v1.endpoints.masters.DtpClient.find_nc_files",
            fake_find_nc_files,
        )

        response = await client.post(
            "/api/v1/masters/products",
            headers=auth_headers,
            json={
                "code": "PROD-DTP",
                "name": "DTP 제품",
                "unit": "EA",
                "dt_project": {
                    "asset_global_id": "https://digital-thread.re/kitech/kimm_project",
                    "asset_id": "https://digital-thread.re/kitech/kimm_project/prj_001",
                    "element_id": "milling_prj",
                    "display_name": "milling_prj",
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["current_dt_project"]["element_id"] == "milling_prj"
        assert [item["workplan_id"] for item in data["current_dt_project"]["workplans"]] == [
            "mainworkplan",
            "wp_001",
        ]

        nc_response = await client.get(
            f"/api/v1/masters/products/{data['id']}/dt-nc-files?workplan_id=wp_001",
            headers=auth_headers,
        )

        assert nc_response.status_code == 200
        nc_files = nc_response.json()
        assert len(nc_files) == 1
        assert nc_files[0]["external_file_id"] == "nc_001"
        assert nc_files[0]["path"] == "/userdata/3/merge.tap"

    @pytest.mark.asyncio
    async def test_create_product_duplicate_code(
        self, client: AsyncClient, auth_headers, sample_product
    ):
        """Duplicate code returns 400."""
        response = await client.post(
            "/api/v1/masters/products",
            headers=auth_headers,
            json={
                "code": "PROD-001",  # Same as sample_product
                "name": "중복 제품",
            },
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_product_missing_required(self, client: AsyncClient, auth_headers):
        """Missing required fields returns 422."""
        response = await client.post(
            "/api/v1/masters/products",
            headers=auth_headers,
            json={"unit": "EA"},  # Missing code and name
        )

        assert response.status_code == 422


class TestProductGet:
    """Test product get endpoint."""

    @pytest.mark.asyncio
    async def test_get_product(self, client: AsyncClient, auth_headers, sample_product):
        """Get a product by ID."""
        response = await client.get(
            f"/api/v1/masters/products/{sample_product.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_product.id
        assert data["code"] == "PROD-001"

    @pytest.mark.asyncio
    async def test_get_product_not_found(self, client: AsyncClient, auth_headers):
        """Non-existent product returns 404."""
        response = await client.get(
            "/api/v1/masters/products/9999",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestProductDelete:
    """Test product deletion endpoint."""

    @pytest.mark.asyncio
    async def test_delete_product(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """Soft delete a product."""
        response = await client.delete(
            f"/api/v1/masters/products/{sample_product.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify soft deletion
        await db_session.refresh(sample_product)
        assert sample_product.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_product_not_found(self, client: AsyncClient, auth_headers):
        """Delete non-existent product returns 404."""
        response = await client.delete(
            "/api/v1/masters/products/9999",
            headers=auth_headers,
        )

        assert response.status_code == 404


# ============================================================================
# QA/QC Regression Tests - PATCH Endpoints
# ============================================================================


class TestStdProcessPatch:
    """Test standard process PATCH endpoint (QA/QC regression)."""

    @pytest.mark.asyncio
    async def test_patch_std_process(self, client: AsyncClient, auth_headers, sample_std_process):
        """PATCH updates standard process fields."""
        response = await client.patch(
            f"/api/v1/masters/std-processes/{sample_std_process.id}",
            headers=auth_headers,
            json={"name": "Updated Process Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Process Name"
        assert data["code"] == sample_std_process.code  # unchanged

    @pytest.mark.asyncio
    async def test_patch_std_process_partial(
        self, client: AsyncClient, auth_headers, sample_std_process
    ):
        """PATCH with partial data only updates specified fields."""
        original_name = sample_std_process.name
        response = await client.patch(
            f"/api/v1/masters/std-processes/{sample_std_process.id}",
            headers=auth_headers,
            json={"equipment_type": "ROBOT"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["equipment_type"] == "ROBOT"
        assert data["name"] == original_name  # unchanged

    @pytest.mark.asyncio
    async def test_patch_std_process_not_found(self, client: AsyncClient, auth_headers):
        """PATCH non-existent process returns 404."""
        response = await client.patch(
            "/api/v1/masters/std-processes/9999",
            headers=auth_headers,
            json={"name": "Test"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_patch_std_process_with_category(
        self, client: AsyncClient, auth_headers, sample_std_process
    ):
        """PATCH response includes category relationship (lazy load regression)."""
        response = await client.patch(
            f"/api/v1/masters/std-processes/{sample_std_process.id}",
            headers=auth_headers,
            json={"name": "Category Test"},
        )

        assert response.status_code == 200
        data = response.json()
        # Should not raise lazy load error - category should be loaded
        assert "category" in data


class TestProductPatch:
    """Test product PATCH endpoint (QA/QC regression)."""

    @pytest.mark.asyncio
    async def test_patch_product(self, client: AsyncClient, auth_headers, sample_product):
        """PATCH updates product fields."""
        response = await client.patch(
            f"/api/v1/masters/products/{sample_product.id}",
            headers=auth_headers,
            json={"name": "Updated Product Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Product Name"
        assert data["code"] == sample_product.code  # unchanged

    @pytest.mark.asyncio
    async def test_patch_product_unit(self, client: AsyncClient, auth_headers, sample_product):
        """PATCH can update unit field."""
        response = await client.patch(
            f"/api/v1/masters/products/{sample_product.id}",
            headers=auth_headers,
            json={"unit": "KG"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["unit"] == "KG"

    @pytest.mark.asyncio
    async def test_patch_product_not_found(self, client: AsyncClient, auth_headers):
        """PATCH non-existent product returns 404."""
        response = await client.patch(
            "/api/v1/masters/products/9999",
            headers=auth_headers,
            json={"name": "Test"},
        )

        assert response.status_code == 404

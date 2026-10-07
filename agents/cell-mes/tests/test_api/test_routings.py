"""Tests for process routing endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from src.app.models.master import ProcessRouting, ProcessRoutingFile, StdProcess


class TestGetProductRoutings:
    """Test get product routings endpoint."""

    @pytest.mark.asyncio
    async def test_get_routings_empty(self, client: AsyncClient, auth_headers, sample_product):
        """Get routings returns empty list when no routings exist."""
        response = await client.get(
            f"/api/v1/masters/products/{sample_product.id}/routings",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_routings_with_data(
        self, client: AsyncClient, auth_headers, sample_product, sample_std_process, db_session
    ):
        """Get routings returns all routings for a product."""
        # Create routing
        routing = ProcessRouting(
            product_id=sample_product.id,
            std_process_id=sample_std_process.id,
            sequence=10,
            remarks="Test routing",
        )
        db_session.add(routing)
        await db_session.flush()

        # Add file to routing
        file = ProcessRoutingFile(
            process_routing_id=routing.id,
            file_type="NC",
            file_path="programs/test.nc",
            sort_order=1,
        )
        db_session.add(file)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/masters/products/{sample_product.id}/routings",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["sequence"] == 10
        assert data[0]["remarks"] == "Test routing"
        assert len(data[0]["files"]) == 1
        assert data[0]["files"][0]["file_type"] == "NC"

    @pytest.mark.asyncio
    async def test_get_routings_product_not_found(self, client: AsyncClient, auth_headers):
        """Get routings for non-existent product returns 404."""
        response = await client.get(
            "/api/v1/masters/products/9999/routings",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_routings_ordered_by_sequence(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """Routings are returned ordered by sequence."""
        # Create multiple std_processes
        processes = []
        for i in range(3):
            process = StdProcess(
                code=f"STD-{i:03d}",
                name=f"Process {i}",
            )
            db_session.add(process)
            processes.append(process)
        await db_session.flush()

        # Create routings in non-sequential order
        for seq, process in zip([30, 10, 20], processes):
            routing = ProcessRouting(
                product_id=sample_product.id,
                std_process_id=process.id,
                sequence=seq,
            )
            db_session.add(routing)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/masters/products/{sample_product.id}/routings",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Check ordering
        assert data[0]["sequence"] == 10
        assert data[1]["sequence"] == 20
        assert data[2]["sequence"] == 30


class TestSaveProductRoutings:
    """Test save product routings endpoint."""

    @pytest.mark.asyncio
    async def test_save_routings(
        self, client: AsyncClient, auth_headers, sample_product, sample_std_process
    ):
        """Save routings for a product."""
        response = await client.put(
            f"/api/v1/masters/products/{sample_product.id}/routings",
            headers=auth_headers,
            json=[
                {
                    "std_process_id": sample_std_process.id,
                    "sequence": 10,
                    "remarks": "First operation",
                    "files": [
                        {
                            "file_type": "NC",
                            "file_path": "programs/op1.nc",
                            "sort_order": 1,
                        }
                    ],
                }
            ],
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["sequence"] == 10
        assert data[0]["cycle_time_sec"] is None
        assert len(data[0]["files"]) == 1

    @pytest.mark.asyncio
    async def test_save_routings_accepts_product_specific_cycle_time(
        self, client: AsyncClient, auth_headers, sample_product, sample_std_process
    ):
        """Save routing-specific cycle time for P4R generation."""
        response = await client.put(
            f"/api/v1/masters/products/{sample_product.id}/routings",
            headers=auth_headers,
            json=[
                {
                    "std_process_id": sample_std_process.id,
                    "sequence": 10,
                    "cycle_time_sec": 417,
                    "cycle_time_breakdown": {
                        "source": "NC_ANALYSIS+PROCESS_INTERNAL",
                        "components": [{"type": "NC_ANALYSIS", "duration_sec": 342}],
                    },
                    "files": [],
                }
            ],
        )

        assert response.status_code == 200
        data = response.json()
        assert data[0]["cycle_time_sec"] == 417
        assert data[0]["cycle_time_breakdown"]["source"] == "NC_ANALYSIS+PROCESS_INTERNAL"

    @pytest.mark.asyncio
    async def test_save_routings_preserves_existing_cycle_time_when_omitted(
        self, client: AsyncClient, auth_headers, sample_product, sample_std_process, db_session
    ):
        """Existing routing-specific time survives full-replace saves from old clients."""
        routing = ProcessRouting(
            product_id=sample_product.id,
            std_process_id=sample_std_process.id,
            sequence=10,
            cycle_time_sec=417,
            cycle_time_breakdown={"source": "manual"},
            remarks="Before",
        )
        db_session.add(routing)
        await db_session.commit()

        response = await client.put(
            f"/api/v1/masters/products/{sample_product.id}/routings",
            headers=auth_headers,
            json=[
                {
                    "std_process_id": sample_std_process.id,
                    "sequence": 10,
                    "remarks": "After",
                    "files": [],
                }
            ],
        )

        assert response.status_code == 200
        data = response.json()
        assert data[0]["remarks"] == "After"
        assert data[0]["cycle_time_sec"] == 417
        assert data[0]["cycle_time_breakdown"] == {"source": "manual"}

    @pytest.mark.asyncio
    async def test_save_routings_replaces_existing(
        self, client: AsyncClient, auth_headers, sample_product, sample_std_process, db_session
    ):
        """Save routings replaces existing routings and their files."""
        # Create initial routing
        routing = ProcessRouting(
            product_id=sample_product.id,
            std_process_id=sample_std_process.id,
            sequence=10,
        )
        db_session.add(routing)
        await db_session.flush()
        old_routing_id = routing.id

        file = ProcessRoutingFile(
            process_routing_id=routing.id,
            file_type="NC",
            file_path="programs/old.nc",
            original_filename="old.nc",
            sort_order=1,
        )
        db_session.add(file)
        await db_session.commit()

        # Create new std_process
        new_process = StdProcess(code="STD-NEW", name="New Process")
        db_session.add(new_process)
        await db_session.commit()

        # Save new routings (should replace)
        response = await client.put(
            f"/api/v1/masters/products/{sample_product.id}/routings",
            headers=auth_headers,
            json=[
                {
                    "std_process_id": new_process.id,
                    "sequence": 20,
                    "remarks": "Replaced routing",
                    "files": [],
                }
            ],
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["sequence"] == 20
        assert data[0]["remarks"] == "Replaced routing"
        assert data[0]["files"] == []

        old_files = await db_session.execute(
            select(ProcessRoutingFile).where(
                ProcessRoutingFile.process_routing_id == old_routing_id
            )
        )
        assert old_files.scalars().all() == []

    @pytest.mark.asyncio
    async def test_save_routings_multiple(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """Save multiple routings at once."""
        # Create multiple std_processes
        processes = []
        for i in range(3):
            process = StdProcess(
                code=f"STD-MULTI-{i:03d}",
                name=f"Multi Process {i}",
            )
            db_session.add(process)
            processes.append(process)
        await db_session.commit()
        await db_session.refresh(processes[0])
        await db_session.refresh(processes[1])
        await db_session.refresh(processes[2])

        response = await client.put(
            f"/api/v1/masters/products/{sample_product.id}/routings",
            headers=auth_headers,
            json=[
                {
                    "std_process_id": processes[0].id,
                    "sequence": 10,
                    "files": [],
                },
                {
                    "std_process_id": processes[1].id,
                    "sequence": 20,
                    "files": [],
                },
                {
                    "std_process_id": processes[2].id,
                    "sequence": 30,
                    "files": [],
                },
            ],
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_save_routings_with_multiple_files(
        self, client: AsyncClient, auth_headers, sample_product, sample_std_process
    ):
        """Save routing with multiple files."""
        response = await client.put(
            f"/api/v1/masters/products/{sample_product.id}/routings",
            headers=auth_headers,
            json=[
                {
                    "std_process_id": sample_std_process.id,
                    "sequence": 10,
                    "files": [
                        {"file_type": "NC", "file_path": "programs/main.nc", "sort_order": 1},
                        {"file_type": "IMAGE", "file_path": "images/setup.png", "sort_order": 2},
                        {"file_type": "DOC", "file_path": "docs/manual.pdf", "sort_order": 3},
                    ],
                }
            ],
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data[0]["files"]) == 3

    @pytest.mark.asyncio
    async def test_save_routings_product_not_found(
        self, client: AsyncClient, auth_headers, sample_std_process
    ):
        """Save routings for non-existent product returns 404."""
        response = await client.put(
            "/api/v1/masters/products/9999/routings",
            headers=auth_headers,
            json=[
                {
                    "std_process_id": sample_std_process.id,
                    "sequence": 10,
                    "files": [],
                }
            ],
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_save_routings_invalid_std_process(
        self, client: AsyncClient, auth_headers, sample_product
    ):
        """Save routings with non-existent std_process returns 400."""
        response = await client.put(
            f"/api/v1/masters/products/{sample_product.id}/routings",
            headers=auth_headers,
            json=[
                {
                    "std_process_id": 9999,
                    "sequence": 10,
                    "files": [],
                }
            ],
        )

        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_save_routings_duplicate_sequence(
        self, client: AsyncClient, auth_headers, sample_product, sample_std_process
    ):
        """Save routings with duplicate sequences returns 400."""
        response = await client.put(
            f"/api/v1/masters/products/{sample_product.id}/routings",
            headers=auth_headers,
            json=[
                {
                    "std_process_id": sample_std_process.id,
                    "sequence": 10,
                    "files": [],
                },
                {
                    "std_process_id": sample_std_process.id,
                    "sequence": 10,  # Duplicate
                    "files": [],
                },
            ],
        )

        assert response.status_code == 400
        assert "Duplicate sequences" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_save_empty_routings(
        self, client: AsyncClient, auth_headers, sample_product, sample_std_process, db_session
    ):
        """Save empty routings list removes all routings."""
        # Create initial routing
        routing = ProcessRouting(
            product_id=sample_product.id,
            std_process_id=sample_std_process.id,
            sequence=10,
        )
        db_session.add(routing)
        await db_session.commit()

        # Save empty list
        response = await client.put(
            f"/api/v1/masters/products/{sample_product.id}/routings",
            headers=auth_headers,
            json=[],
        )

        assert response.status_code == 200
        assert response.json() == []

        # Verify routings are deleted
        get_response = await client.get(
            f"/api/v1/masters/products/{sample_product.id}/routings",
            headers=auth_headers,
        )
        assert get_response.json() == []


# ============================================================================
# QA/QC Regression Tests - Path Validation
# ============================================================================


class TestPathValidation:
    """Test file path validation (QA/QC regression)."""

    @pytest.mark.asyncio
    async def test_absolute_path_allowed(
        self, client: AsyncClient, auth_headers, sample_product, sample_std_process
    ):
        """Absolute paths should be allowed (regression: was 500 error)."""
        response = await client.put(
            f"/api/v1/masters/products/{sample_product.id}/routings",
            headers=auth_headers,
            json=[
                {
                    "std_process_id": sample_std_process.id,
                    "sequence": 10,
                    "files": [
                        {
                            "file_type": "NC",
                            "file_path": "/absolute/path/program.nc",
                            "sort_order": 1,
                        }
                    ],
                }
            ],
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["files"][0]["file_path"] == "/absolute/path/program.nc"

    @pytest.mark.asyncio
    async def test_relative_path_allowed(
        self, client: AsyncClient, auth_headers, sample_product, sample_std_process
    ):
        """Relative paths should work normally."""
        response = await client.put(
            f"/api/v1/masters/products/{sample_product.id}/routings",
            headers=auth_headers,
            json=[
                {
                    "std_process_id": sample_std_process.id,
                    "sequence": 10,
                    "files": [
                        {
                            "file_type": "NC",
                            "file_path": "programs/subfolder/test.nc",
                            "sort_order": 1,
                        }
                    ],
                }
            ],
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_path_traversal_blocked(
        self, client: AsyncClient, auth_headers, sample_product, sample_std_process
    ):
        """Path traversal (../) should be blocked for security."""
        response = await client.put(
            f"/api/v1/masters/products/{sample_product.id}/routings",
            headers=auth_headers,
            json=[
                {
                    "std_process_id": sample_std_process.id,
                    "sequence": 10,
                    "files": [
                        {
                            "file_type": "NC",
                            "file_path": "../../../etc/passwd",
                            "sort_order": 1,
                        }
                    ],
                }
            ],
        )

        assert response.status_code == 422
        assert "traversal" in response.json()["detail"][0]["msg"].lower()

    @pytest.mark.asyncio
    async def test_special_chars_in_filename(
        self, client: AsyncClient, auth_headers, sample_product, sample_std_process
    ):
        """Filenames with allowed special chars (hyphen, underscore) should work."""
        response = await client.put(
            f"/api/v1/masters/products/{sample_product.id}/routings",
            headers=auth_headers,
            json=[
                {
                    "std_process_id": sample_std_process.id,
                    "sequence": 10,
                    "files": [
                        {
                            "file_type": "NC",
                            "file_path": "programs/test-file_v2.nc",
                            "sort_order": 1,
                        }
                    ],
                }
            ],
        )

        assert response.status_code == 200

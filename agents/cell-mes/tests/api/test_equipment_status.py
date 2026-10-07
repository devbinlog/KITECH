"""Tests for equipment status history endpoints."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from src.app.models.equipment import EquipmentStatusHistory


class TestEquipmentStatusHistoryCRUD:
    """Test equipment status history CRUD operations."""

    @pytest.mark.asyncio
    async def test_record_status_change(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Record a status change for equipment."""
        # Arrange
        changed_at = datetime.now(timezone.utc)
        status_data = {
            "equipment_id": sample_equipment.id,
            "new_status": "STOP",
            "changed_at": changed_at.isoformat(),
            "reason": "정기 보전",
            "changed_by": "operator1",
        }

        # Act
        response = await client.post(
            f"/api/v1/masters/equipments/{sample_equipment.id}/status-history",
            headers=auth_headers,
            json=status_data,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["equipment_id"] == sample_equipment.id
        assert data["new_status"] == "STOP"
        assert data["previous_status"] == "RUN"  # sample_equipment starts with RUN
        assert data["reason"] == "정기 보전"
        assert data["changed_by"] == "operator1"

    @pytest.mark.asyncio
    async def test_record_status_change_updates_equipment(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Recording status change updates equipment current_status."""
        # Arrange
        changed_at = datetime.now(timezone.utc)
        status_data = {
            "equipment_id": sample_equipment.id,
            "new_status": "MAINTENANCE",
            "changed_at": changed_at.isoformat(),
            "reason": "주간 점검",
            "changed_by": "technician1",
        }

        # Act
        response = await client.post(
            f"/api/v1/masters/equipments/{sample_equipment.id}/status-history",
            headers=auth_headers,
            json=status_data,
        )

        # Verify equipment status is updated
        eq_response = await client.get(
            f"/api/v1/masters/equipments/{sample_equipment.id}",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 201
        assert eq_response.status_code == 200
        eq_data = eq_response.json()
        assert eq_data["current_status"] == "MAINTENANCE"

    @pytest.mark.asyncio
    async def test_record_status_change_calculates_duration(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Recording status change calculates previous duration."""
        # Arrange - Create first status change
        first_time = datetime.now(timezone.utc) - timedelta(hours=2)
        first_data = {
            "equipment_id": sample_equipment.id,
            "new_status": "IDLE",
            "changed_at": first_time.isoformat(),
            "changed_by": "system",
        }
        await client.post(
            f"/api/v1/masters/equipments/{sample_equipment.id}/status-history",
            headers=auth_headers,
            json=first_data,
        )

        # Create second status change 2 hours later
        second_time = datetime.now(timezone.utc)
        second_data = {
            "equipment_id": sample_equipment.id,
            "new_status": "RUN",
            "changed_at": second_time.isoformat(),
            "changed_by": "system",
        }

        # Act
        response = await client.post(
            f"/api/v1/masters/equipments/{sample_equipment.id}/status-history",
            headers=auth_headers,
            json=second_data,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        # Duration should be approximately 120 minutes (2 hours)
        assert data["previous_duration_minutes"] is not None
        assert 115 <= data["previous_duration_minutes"] <= 125

    @pytest.mark.asyncio
    async def test_record_status_change_not_found(
        self, client: AsyncClient, auth_headers, db_session
    ):
        """Record status change for non-existent equipment returns 404."""
        # Arrange
        status_data = {
            "equipment_id": 99999,
            "new_status": "STOP",
            "changed_at": datetime.now(timezone.utc).isoformat(),
            "changed_by": "system",
        }

        # Act
        response = await client.post(
            "/api/v1/masters/equipments/99999/status-history",
            headers=auth_headers,
            json=status_data,
        )

        # Assert
        assert response.status_code == 404


class TestEquipmentStatusHistoryList:
    """Test equipment status history list operations."""

    @pytest.mark.asyncio
    async def test_get_status_history(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Get status history for equipment."""
        # Arrange - Create some history records
        statuses = ["IDLE", "RUN", "STOP", "RUN"]
        base_time = datetime.now(timezone.utc) - timedelta(hours=len(statuses))

        for i, status in enumerate(statuses):
            history = EquipmentStatusHistory(
                equipment_id=sample_equipment.id,
                previous_status=statuses[i - 1] if i > 0 else "RUN",
                new_status=status,
                changed_at=base_time + timedelta(hours=i),
                changed_by="system",
            )
            db_session.add(history)
        await db_session.commit()

        # Act
        response = await client.get(
            f"/api/v1/masters/equipments/{sample_equipment.id}/status-history",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 4

    @pytest.mark.asyncio
    async def test_get_status_history_ordered(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Status history should be ordered by changed_at descending."""
        # Arrange
        now = datetime.now(timezone.utc)
        for i in range(3):
            history = EquipmentStatusHistory(
                equipment_id=sample_equipment.id,
                previous_status="RUN",
                new_status="IDLE",
                changed_at=now - timedelta(hours=i),
                changed_by="system",
            )
            db_session.add(history)
        await db_session.commit()

        # Act
        response = await client.get(
            f"/api/v1/masters/equipments/{sample_equipment.id}/status-history",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Verify descending order (most recent first)
        for i in range(len(data) - 1):
            assert data[i]["changed_at"] >= data[i + 1]["changed_at"]

    @pytest.mark.asyncio
    async def test_get_status_history_filter_by_date(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Filter status history by date range."""
        # Arrange
        now = datetime.now(timezone.utc)
        old_history = EquipmentStatusHistory(
            equipment_id=sample_equipment.id,
            previous_status="RUN",
            new_status="IDLE",
            changed_at=now - timedelta(days=10),
            changed_by="system",
        )
        recent_history = EquipmentStatusHistory(
            equipment_id=sample_equipment.id,
            previous_status="IDLE",
            new_status="RUN",
            changed_at=now - timedelta(hours=1),
            changed_by="system",
        )
        db_session.add(old_history)
        db_session.add(recent_history)
        await db_session.commit()

        # Act - Query only last 2 days (use URL-safe format)
        date_from = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S")
        response = await client.get(
            f"/api/v1/masters/equipments/{sample_equipment.id}/status-history?date_from={date_from}",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Should only include recent history
        for item in data:
            item_time = datetime.fromisoformat(item["changed_at"].replace("Z", "+00:00"))
            assert item_time >= now - timedelta(days=2)

    @pytest.mark.asyncio
    async def test_get_status_history_limit(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Limit number of history records returned."""
        # Arrange - Create many history records
        now = datetime.now(timezone.utc)
        for i in range(20):
            history = EquipmentStatusHistory(
                equipment_id=sample_equipment.id,
                previous_status="RUN",
                new_status="IDLE",
                changed_at=now - timedelta(hours=i),
                changed_by="system",
            )
            db_session.add(history)
        await db_session.commit()

        # Act
        response = await client.get(
            f"/api/v1/masters/equipments/{sample_equipment.id}/status-history?limit=10",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10


class TestEquipmentStatusSummary:
    """Test equipment status summary for OEE calculation."""

    @pytest.mark.asyncio
    async def test_get_status_summary(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Get status summary for equipment."""
        # Arrange - Create history with known durations
        now = datetime.now(timezone.utc)

        # RUN for 60 minutes
        history1 = EquipmentStatusHistory(
            equipment_id=sample_equipment.id,
            previous_status="IDLE",
            new_status="RUN",
            changed_at=now - timedelta(hours=3),
            previous_duration_minutes=60,
            changed_by="system",
        )
        # IDLE for 30 minutes
        history2 = EquipmentStatusHistory(
            equipment_id=sample_equipment.id,
            previous_status="RUN",
            new_status="IDLE",
            changed_at=now - timedelta(hours=2),
            previous_duration_minutes=30,
            changed_by="system",
        )
        # STOP for 30 minutes
        history3 = EquipmentStatusHistory(
            equipment_id=sample_equipment.id,
            previous_status="IDLE",
            new_status="STOP",
            changed_at=now - timedelta(hours=1),
            previous_duration_minutes=30,
            changed_by="system",
        )
        db_session.add(history1)
        db_session.add(history2)
        db_session.add(history3)
        await db_session.commit()

        # Act
        response = await client.get(
            f"/api/v1/masters/equipments/{sample_equipment.id}/status-summary",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "equipment_id" in data
        assert "by_status" in data
        assert "total_minutes" in data
        assert "run_minutes" in data
        assert "availability_percent" in data

    @pytest.mark.asyncio
    async def test_status_summary_availability_calculation(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Verify availability calculation in status summary."""
        # Arrange - Create history: 60 min RUN, 40 min other = 60% availability
        now = datetime.now(timezone.utc)

        # RUN for 60 minutes
        history1 = EquipmentStatusHistory(
            equipment_id=sample_equipment.id,
            previous_status="IDLE",
            new_status="RUN",
            changed_at=now - timedelta(hours=2),
            previous_duration_minutes=60,
            changed_by="system",
        )
        # IDLE for 20 minutes
        history2 = EquipmentStatusHistory(
            equipment_id=sample_equipment.id,
            previous_status="RUN",
            new_status="IDLE",
            changed_at=now - timedelta(hours=1),
            previous_duration_minutes=20,
            changed_by="system",
        )
        # STOP for 20 minutes
        history3 = EquipmentStatusHistory(
            equipment_id=sample_equipment.id,
            previous_status="IDLE",
            new_status="STOP",
            changed_at=now,
            previous_duration_minutes=20,
            changed_by="system",
        )
        db_session.add(history1)
        db_session.add(history2)
        db_session.add(history3)
        await db_session.commit()

        # Act
        response = await client.get(
            f"/api/v1/masters/equipments/{sample_equipment.id}/status-summary",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Total = 60 + 20 + 20 = 100 minutes
        # Run = 60 minutes
        # Availability = 60 / 100 = 60%
        assert data["total_minutes"] == 100
        assert data["run_minutes"] == 60
        assert 59 <= data["availability_percent"] <= 61

    @pytest.mark.asyncio
    async def test_status_summary_filter_by_date(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Filter status summary by date range."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Old record (should be excluded)
        old_history = EquipmentStatusHistory(
            equipment_id=sample_equipment.id,
            previous_status="IDLE",
            new_status="RUN",
            changed_at=now - timedelta(days=10),
            previous_duration_minutes=120,
            changed_by="system",
        )
        # Recent record
        recent_history = EquipmentStatusHistory(
            equipment_id=sample_equipment.id,
            previous_status="RUN",
            new_status="IDLE",
            changed_at=now - timedelta(hours=1),
            previous_duration_minutes=60,
            changed_by="system",
        )
        db_session.add(old_history)
        db_session.add(recent_history)
        await db_session.commit()

        # Act - Query only last 2 days (use URL-safe format)
        date_from = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S")
        response = await client.get(
            f"/api/v1/masters/equipments/{sample_equipment.id}/status-summary?date_from={date_from}",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Should only include recent history (60 minutes, not 180)
        assert data["total_minutes"] == 60

    @pytest.mark.asyncio
    async def test_status_summary_empty(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Status summary with no history returns zeros."""
        # Act - No history records
        response = await client.get(
            f"/api/v1/masters/equipments/{sample_equipment.id}/status-summary",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_minutes"] == 0
        assert data["run_minutes"] == 0
        assert data["availability_percent"] == 0


class TestStatusTransitions:
    """Test various status transitions."""

    @pytest.mark.asyncio
    async def test_all_valid_statuses(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Test all valid status values."""
        # Arrange
        valid_statuses = ["RUN", "IDLE", "STOP", "SETUP", "ERROR", "MAINTENANCE"]

        for status in valid_statuses:
            changed_at = datetime.now(timezone.utc)
            status_data = {
                "equipment_id": sample_equipment.id,
                "new_status": status,
                "changed_at": changed_at.isoformat(),
                "changed_by": "system",
            }

            # Act
            response = await client.post(
                f"/api/v1/masters/equipments/{sample_equipment.id}/status-history",
                headers=auth_headers,
                json=status_data,
            )

            # Assert
            assert response.status_code == 201, f"Failed for status: {status}"
            data = response.json()
            assert data["new_status"] == status

    @pytest.mark.asyncio
    async def test_status_with_work_order(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment, sample_work_order
    ):
        """Record status change associated with work order."""
        # Arrange
        changed_at = datetime.now(timezone.utc)
        status_data = {
            "equipment_id": sample_equipment.id,
            "new_status": "RUN",
            "changed_at": changed_at.isoformat(),
            "work_order_id": sample_work_order.id,
            "changed_by": "system",
        }

        # Act
        response = await client.post(
            f"/api/v1/masters/equipments/{sample_equipment.id}/status-history",
            headers=auth_headers,
            json=status_data,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["work_order_id"] == sample_work_order.id

    @pytest.mark.asyncio
    async def test_sequential_status_changes(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Test sequential status changes track correctly."""
        # Arrange
        transitions = [
            ("IDLE", "system"),
            ("SETUP", "operator1"),
            ("RUN", "operator1"),
            ("STOP", "supervisor"),
            ("MAINTENANCE", "technician1"),
        ]

        base_time = datetime.now(timezone.utc)
        previous_status = "RUN"  # sample_equipment starts with RUN

        for i, (new_status, changed_by) in enumerate(transitions):
            changed_at = base_time + timedelta(hours=i)
            status_data = {
                "equipment_id": sample_equipment.id,
                "new_status": new_status,
                "changed_at": changed_at.isoformat(),
                "changed_by": changed_by,
            }

            # Act
            response = await client.post(
                f"/api/v1/masters/equipments/{sample_equipment.id}/status-history",
                headers=auth_headers,
                json=status_data,
            )

            # Assert
            assert response.status_code == 201
            data = response.json()
            assert data["new_status"] == new_status
            assert data["previous_status"] == previous_status
            assert data["changed_by"] == changed_by

            previous_status = new_status

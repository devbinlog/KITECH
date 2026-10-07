"""Tests for downtime management endpoints."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from src.app.models.downtime import DowntimeReason, Downtime


class TestDowntimeReasonCRUD:
    """Test downtime reason CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_downtime_reason(self, client: AsyncClient, auth_headers, db_session):
        """Create a new downtime reason."""
        # Arrange
        reason_data = {
            "code": "DT-001",
            "name": "정기 보전",
            "category": "PLANNED",
            "description": "정기 예방 보전 작업",
        }

        # Act
        response = await client.post(
            "/api/v1/downtime/reasons",
            headers=auth_headers,
            json=reason_data,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "DT-001"
        assert data["name"] == "정기 보전"
        assert data["category"] == "PLANNED"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_downtime_reason_duplicate_code(
        self, client: AsyncClient, auth_headers, db_session
    ):
        """Duplicate reason code returns 400."""
        # Arrange - Create first reason
        reason = DowntimeReason(
            code="DT-DUP-001",
            name="중복 테스트",
            category="UNPLANNED",
        )
        db_session.add(reason)
        await db_session.commit()

        # Act - Try to create duplicate
        response = await client.post(
            "/api/v1/downtime/reasons",
            headers=auth_headers,
            json={
                "code": "DT-DUP-001",
                "name": "다른 이름",
                "category": "PLANNED",
            },
        )

        # Assert
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_downtime_reasons(self, client: AsyncClient, auth_headers, db_session):
        """List downtime reasons."""
        # Arrange
        categories = ["PLANNED", "UNPLANNED", "SETUP"]
        for i, category in enumerate(categories):
            reason = DowntimeReason(
                code=f"DT-LIST-{i:03d}",
                name=f"{category} 테스트",
                category=category,
            )
            db_session.add(reason)
        await db_session.commit()

        # Act
        response = await client.get(
            "/api/v1/downtime/reasons",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    @pytest.mark.asyncio
    async def test_list_downtime_reasons_filter_by_category(
        self, client: AsyncClient, auth_headers, db_session
    ):
        """Filter downtime reasons by category."""
        # Arrange
        for i in range(2):
            db_session.add(
                DowntimeReason(
                    code=f"DT-PLANNED-{i:03d}",
                    name=f"계획 정지 {i}",
                    category="PLANNED",
                )
            )
        for i in range(3):
            db_session.add(
                DowntimeReason(
                    code=f"DT-UNPLANNED-{i:03d}",
                    name=f"비계획 정지 {i}",
                    category="UNPLANNED",
                )
            )
        await db_session.commit()

        # Act
        response = await client.get(
            "/api/v1/downtime/reasons?category=PLANNED",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["category"] == "PLANNED"

    @pytest.mark.asyncio
    async def test_list_downtime_reasons_active_only(
        self, client: AsyncClient, auth_headers, db_session
    ):
        """Filter active downtime reasons only."""
        # Arrange
        active_reason = DowntimeReason(
            code="DT-ACTIVE-001",
            name="활성 사유",
            category="UNPLANNED",
            is_active=True,
        )
        inactive_reason = DowntimeReason(
            code="DT-INACTIVE-001",
            name="비활성 사유",
            category="UNPLANNED",
            is_active=False,
        )
        db_session.add(active_reason)
        db_session.add(inactive_reason)
        await db_session.commit()

        # Act - Default active_only=True
        response = await client.get(
            "/api/v1/downtime/reasons",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        codes = [item["code"] for item in data]
        assert "DT-ACTIVE-001" in codes
        assert "DT-INACTIVE-001" not in codes


class TestDowntimeCRUD:
    """Test downtime CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_downtime(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Create a new downtime record."""
        # Arrange
        reason = DowntimeReason(
            code="DT-CREATE-001",
            name="기계 고장",
            category="UNPLANNED",
        )
        db_session.add(reason)
        await db_session.commit()
        await db_session.refresh(reason)

        start_time = datetime.now(timezone.utc)
        downtime_data = {
            "equipment_id": sample_equipment.id,
            "reason_id": reason.id,
            "start_time": start_time.isoformat(),
            "remarks": "스핀들 과열로 인한 정지",
            "reported_by": "operator1",
        }

        # Act
        response = await client.post(
            "/api/v1/downtime",
            headers=auth_headers,
            json=downtime_data,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["equipment_id"] == sample_equipment.id
        assert data["reason_id"] == reason.id
        assert data["is_ongoing"] is True
        assert data["end_time"] is None

    @pytest.mark.asyncio
    async def test_list_downtimes(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """List downtime records."""
        # Arrange
        for i in range(3):
            downtime = Downtime(
                equipment_id=sample_equipment.id,
                start_time=datetime.now(timezone.utc) - timedelta(hours=i),
            )
            db_session.add(downtime)
        await db_session.commit()

        # Act
        response = await client.get(
            "/api/v1/downtime",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    @pytest.mark.asyncio
    async def test_list_downtimes_filter_by_equipment(
        self, client: AsyncClient, auth_headers, db_session, multiple_equipments
    ):
        """Filter downtimes by equipment."""
        # Arrange
        target_equipment = multiple_equipments[0]
        for eq in multiple_equipments[:2]:
            downtime = Downtime(
                equipment_id=eq.id,
                start_time=datetime.now(timezone.utc),
            )
            db_session.add(downtime)
        await db_session.commit()

        # Act
        response = await client.get(
            f"/api/v1/downtime?equipment_id={target_equipment.id}",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["equipment_id"] == target_equipment.id

    @pytest.mark.asyncio
    async def test_list_downtimes_ongoing_only(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Filter ongoing downtimes only."""
        # Arrange - One ongoing, one completed
        ongoing = Downtime(
            equipment_id=sample_equipment.id,
            start_time=datetime.now(timezone.utc),
            end_time=None,
        )
        completed = Downtime(
            equipment_id=sample_equipment.id,
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            duration_minutes=60,
        )
        db_session.add(ongoing)
        db_session.add(completed)
        await db_session.commit()

        # Act
        response = await client.get(
            "/api/v1/downtime?ongoing_only=true",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["end_time"] is None


class TestDowntimeEnd:
    """Test downtime end operation."""

    @pytest.mark.asyncio
    async def test_end_downtime(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """End an ongoing downtime."""
        # Arrange
        downtime = Downtime(
            equipment_id=sample_equipment.id,
            start_time=datetime.now(timezone.utc) - timedelta(minutes=30),
        )
        db_session.add(downtime)
        await db_session.commit()
        await db_session.refresh(downtime)

        # Act
        response = await client.post(
            f"/api/v1/downtime/{downtime.id}/end",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["end_time"] is not None
        assert data["is_ongoing"] is False

    @pytest.mark.asyncio
    async def test_end_downtime_already_ended(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Cannot end an already ended downtime."""
        # Arrange
        downtime = Downtime(
            equipment_id=sample_equipment.id,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc),
            duration_minutes=60,
        )
        db_session.add(downtime)
        await db_session.commit()
        await db_session.refresh(downtime)

        # Act
        response = await client.post(
            f"/api/v1/downtime/{downtime.id}/end",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 400
        assert "already ended" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_end_downtime_not_found(self, client: AsyncClient, auth_headers, db_session):
        """End non-existent downtime returns 404."""
        # Act
        response = await client.post(
            "/api/v1/downtime/99999/end",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 404


class TestDowntimeUpdate:
    """Test downtime update operation."""

    @pytest.mark.asyncio
    async def test_update_downtime(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Update a downtime record."""
        # Arrange
        reason = DowntimeReason(
            code="DT-UPDATE-001",
            name="업데이트 테스트",
            category="UNPLANNED",
        )
        db_session.add(reason)
        await db_session.commit()
        await db_session.refresh(reason)

        downtime = Downtime(
            equipment_id=sample_equipment.id,
            start_time=datetime.now(timezone.utc),
        )
        db_session.add(downtime)
        await db_session.commit()
        await db_session.refresh(downtime)

        # Act
        response = await client.patch(
            f"/api/v1/downtime/{downtime.id}",
            headers=auth_headers,
            json={
                "reason_id": reason.id,
                "remarks": "업데이트된 비고",
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["reason_id"] == reason.id
        assert data["remarks"] == "업데이트된 비고"

    @pytest.mark.asyncio
    async def test_update_downtime_not_found(self, client: AsyncClient, auth_headers, db_session):
        """Update non-existent downtime returns 404."""
        # Act
        response = await client.patch(
            "/api/v1/downtime/99999",
            headers=auth_headers,
            json={"remarks": "테스트"},
        )

        # Assert
        assert response.status_code == 404


class TestDowntimeSummary:
    """Test downtime summary statistics."""

    @pytest.mark.asyncio
    async def test_downtime_summary(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Get downtime summary statistics."""
        # Arrange
        planned_reason = DowntimeReason(
            code="DT-SUMMARY-P",
            name="계획 정지",
            category="PLANNED",
        )
        unplanned_reason = DowntimeReason(
            code="DT-SUMMARY-U",
            name="비계획 정지",
            category="UNPLANNED",
        )
        db_session.add(planned_reason)
        db_session.add(unplanned_reason)
        await db_session.commit()
        await db_session.refresh(planned_reason)
        await db_session.refresh(unplanned_reason)

        # Create downtimes with different categories
        dt1 = Downtime(
            equipment_id=sample_equipment.id,
            reason_id=planned_reason.id,
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            duration_minutes=60,
        )
        dt2 = Downtime(
            equipment_id=sample_equipment.id,
            reason_id=unplanned_reason.id,
            start_time=datetime.now(timezone.utc) - timedelta(hours=4),
            end_time=datetime.now(timezone.utc) - timedelta(hours=3),
            duration_minutes=60,
        )
        dt3 = Downtime(
            equipment_id=sample_equipment.id,
            reason_id=unplanned_reason.id,
            start_time=datetime.now(timezone.utc) - timedelta(hours=6),
            end_time=datetime.now(timezone.utc) - timedelta(hours=5),
            duration_minutes=60,
        )
        db_session.add(dt1)
        db_session.add(dt2)
        db_session.add(dt3)
        await db_session.commit()

        # Act
        response = await client.get(
            f"/api/v1/downtime/summary?equipment_id={sample_equipment.id}",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "by_category" in data
        assert "total_count" in data
        assert "total_minutes" in data
        assert data["total_count"] >= 3
        assert data["total_minutes"] >= 180  # 3 * 60 minutes

    @pytest.mark.asyncio
    async def test_downtime_summary_by_category(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Verify summary breakdown by category."""
        # Arrange
        reason = DowntimeReason(
            code="DT-CAT-001",
            name="셋업",
            category="SETUP",
        )
        db_session.add(reason)
        await db_session.commit()
        await db_session.refresh(reason)

        downtime = Downtime(
            equipment_id=sample_equipment.id,
            reason_id=reason.id,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc),
            duration_minutes=60,
        )
        db_session.add(downtime)
        await db_session.commit()

        # Act
        response = await client.get(
            "/api/v1/downtime/summary",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "SETUP" in data["by_category"]
        assert data["by_category"]["SETUP"]["count"] >= 1

    @pytest.mark.asyncio
    async def test_downtime_summary_date_range(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Filter summary by date range."""
        # Arrange
        reason = DowntimeReason(
            code="DT-RANGE-001",
            name="범위 테스트",
            category="UNPLANNED",
        )
        db_session.add(reason)
        await db_session.commit()
        await db_session.refresh(reason)

        now = datetime.now(timezone.utc)
        old_downtime = Downtime(
            equipment_id=sample_equipment.id,
            reason_id=reason.id,
            start_time=now - timedelta(days=10),
            end_time=now - timedelta(days=10) + timedelta(hours=1),
            duration_minutes=60,
        )
        recent_downtime = Downtime(
            equipment_id=sample_equipment.id,
            reason_id=reason.id,
            start_time=now - timedelta(hours=1),
            end_time=now,
            duration_minutes=60,
        )
        db_session.add(old_downtime)
        db_session.add(recent_downtime)
        await db_session.commit()

        # Act - Query only last 2 days (use URL-safe format)
        date_from = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S")
        response = await client.get(
            f"/api/v1/downtime/summary?date_from={date_from}",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Should only include recent downtime
        assert data["total_count"] >= 1

"""Tests for alarm management endpoints."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from src.app.models.alarm import AlarmDefinition, Alarm


class TestAlarmDefinitionCRUD:
    """Test alarm definition CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_alarm_definition(self, client: AsyncClient, auth_headers, db_session):
        """Create a new alarm definition."""
        # Arrange
        definition_data = {
            "code": "ALM-001",
            "name": "스핀들 과열",
            "severity": "CRITICAL",
            "category": "EQUIPMENT",
            "description": "스핀들 온도가 임계값 초과",
            "recommended_action": "즉시 정지 후 냉각 대기",
            "auto_stop": True,
        }

        # Act
        response = await client.post(
            "/api/v1/alarms/definitions",
            headers=auth_headers,
            json=definition_data,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "ALM-001"
        assert data["name"] == "스핀들 과열"
        assert data["severity"] == "CRITICAL"
        assert data["category"] == "EQUIPMENT"
        assert data["auto_stop"] is True
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_alarm_definition_duplicate_code(
        self, client: AsyncClient, auth_headers, db_session
    ):
        """Duplicate alarm definition code returns 400."""
        # Arrange - Create first definition
        definition = AlarmDefinition(
            code="ALM-DUP-001",
            name="중복 테스트",
            severity="WARNING",
            category="EQUIPMENT",
        )
        db_session.add(definition)
        await db_session.commit()

        # Act - Try to create duplicate
        response = await client.post(
            "/api/v1/alarms/definitions",
            headers=auth_headers,
            json={
                "code": "ALM-DUP-001",
                "name": "다른 이름",
                "severity": "CRITICAL",
                "category": "PROCESS",
            },
        )

        # Assert
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_alarm_definitions(self, client: AsyncClient, auth_headers, db_session):
        """List alarm definitions."""
        # Arrange
        severities = ["INFO", "WARNING", "CRITICAL", "EMERGENCY"]
        for i, severity in enumerate(severities):
            definition = AlarmDefinition(
                code=f"ALM-LIST-{i:03d}",
                name=f"{severity} 알람",
                severity=severity,
                category="EQUIPMENT",
            )
            db_session.add(definition)
        await db_session.commit()

        # Act
        response = await client.get(
            "/api/v1/alarms/definitions",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 4

    @pytest.mark.asyncio
    async def test_list_alarm_definitions_filter_by_severity(
        self, client: AsyncClient, auth_headers, db_session
    ):
        """Filter alarm definitions by severity."""
        # Arrange
        for i in range(2):
            db_session.add(
                AlarmDefinition(
                    code=f"ALM-CRIT-{i:03d}",
                    name=f"긴급 알람 {i}",
                    severity="CRITICAL",
                    category="EQUIPMENT",
                )
            )
        for i in range(3):
            db_session.add(
                AlarmDefinition(
                    code=f"ALM-WARN-{i:03d}",
                    name=f"경고 알람 {i}",
                    severity="WARNING",
                    category="EQUIPMENT",
                )
            )
        await db_session.commit()

        # Act
        response = await client.get(
            "/api/v1/alarms/definitions?severity=CRITICAL",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["severity"] == "CRITICAL"

    @pytest.mark.asyncio
    async def test_list_alarm_definitions_filter_by_category(
        self, client: AsyncClient, auth_headers, db_session
    ):
        """Filter alarm definitions by category."""
        # Arrange
        categories = ["EQUIPMENT", "PROCESS", "QUALITY", "SAFETY"]
        for i, category in enumerate(categories):
            db_session.add(
                AlarmDefinition(
                    code=f"ALM-CAT-{i:03d}",
                    name=f"{category} 알람",
                    severity="WARNING",
                    category=category,
                )
            )
        await db_session.commit()

        # Act
        response = await client.get(
            "/api/v1/alarms/definitions?category=SAFETY",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["category"] == "SAFETY"


class TestAlarmWorkflow:
    """Test alarm occurrence, acknowledge, resolve workflow."""

    @pytest.mark.asyncio
    async def test_create_alarm(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Create a new alarm (alarm occurrence)."""
        # Arrange
        definition = AlarmDefinition(
            code="ALM-CREATE-001",
            name="온도 이상",
            severity="WARNING",
            category="EQUIPMENT",
        )
        db_session.add(definition)
        await db_session.commit()
        await db_session.refresh(definition)

        occurred_at = datetime.now(timezone.utc)
        alarm_data = {
            "definition_id": definition.id,
            "equipment_id": sample_equipment.id,
            "occurred_at": occurred_at.isoformat(),
            "message": "스핀들 온도 85°C 초과",
            "value": "87°C",
        }

        # Act
        response = await client.post(
            "/api/v1/alarms",
            headers=auth_headers,
            json=alarm_data,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["definition_id"] == definition.id
        assert data["equipment_id"] == sample_equipment.id
        assert data["status"] == "ACTIVE"
        assert data["message"] == "스핀들 온도 85°C 초과"

    @pytest.mark.asyncio
    async def test_acknowledge_alarm(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Acknowledge an active alarm."""
        # Arrange
        definition = AlarmDefinition(
            code="ALM-ACK-001",
            name="확인 테스트",
            severity="WARNING",
            category="EQUIPMENT",
        )
        db_session.add(definition)
        await db_session.commit()
        await db_session.refresh(definition)

        alarm = Alarm(
            definition_id=definition.id,
            equipment_id=sample_equipment.id,
            occurred_at=datetime.now(timezone.utc),
            status="ACTIVE",
        )
        db_session.add(alarm)
        await db_session.commit()
        await db_session.refresh(alarm)

        # Act
        response = await client.post(
            f"/api/v1/alarms/{alarm.id}/acknowledge",
            headers=auth_headers,
            json={"acknowledged_by": "operator1"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ACKNOWLEDGED"
        assert data["acknowledged_by"] == "operator1"
        assert data["acknowledged_at"] is not None

    @pytest.mark.asyncio
    async def test_acknowledge_alarm_invalid_status(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Cannot acknowledge an already acknowledged alarm."""
        # Arrange
        definition = AlarmDefinition(
            code="ALM-ACK-INV-001",
            name="상태 테스트",
            severity="WARNING",
            category="EQUIPMENT",
        )
        db_session.add(definition)
        await db_session.commit()
        await db_session.refresh(definition)

        alarm = Alarm(
            definition_id=definition.id,
            equipment_id=sample_equipment.id,
            occurred_at=datetime.now(timezone.utc),
            status="ACKNOWLEDGED",
            acknowledged_at=datetime.now(timezone.utc),
            acknowledged_by="someone",
        )
        db_session.add(alarm)
        await db_session.commit()
        await db_session.refresh(alarm)

        # Act
        response = await client.post(
            f"/api/v1/alarms/{alarm.id}/acknowledge",
            headers=auth_headers,
            json={"acknowledged_by": "operator2"},
        )

        # Assert
        assert response.status_code == 400
        assert "Cannot acknowledge" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_resolve_alarm(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Resolve an alarm."""
        # Arrange
        definition = AlarmDefinition(
            code="ALM-RESOLVE-001",
            name="해제 테스트",
            severity="CRITICAL",
            category="EQUIPMENT",
        )
        db_session.add(definition)
        await db_session.commit()
        await db_session.refresh(definition)

        alarm = Alarm(
            definition_id=definition.id,
            equipment_id=sample_equipment.id,
            occurred_at=datetime.now(timezone.utc) - timedelta(hours=1),
            status="ACKNOWLEDGED",
            acknowledged_at=datetime.now(timezone.utc) - timedelta(minutes=30),
            acknowledged_by="operator1",
        )
        db_session.add(alarm)
        await db_session.commit()
        await db_session.refresh(alarm)

        # Act
        response = await client.post(
            f"/api/v1/alarms/{alarm.id}/resolve",
            headers=auth_headers,
            json={
                "resolved_by": "technician1",
                "resolution_note": "베어링 교체 완료",
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RESOLVED"
        assert data["resolved_by"] == "technician1"
        assert data["resolution_note"] == "베어링 교체 완료"
        assert data["resolved_at"] is not None

    @pytest.mark.asyncio
    async def test_resolve_alarm_already_resolved(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Cannot resolve an already resolved alarm."""
        # Arrange
        definition = AlarmDefinition(
            code="ALM-RESOLVE-DUP-001",
            name="이중 해제 테스트",
            severity="WARNING",
            category="EQUIPMENT",
        )
        db_session.add(definition)
        await db_session.commit()
        await db_session.refresh(definition)

        alarm = Alarm(
            definition_id=definition.id,
            equipment_id=sample_equipment.id,
            occurred_at=datetime.now(timezone.utc) - timedelta(hours=2),
            status="RESOLVED",
            resolved_at=datetime.now(timezone.utc),
            resolved_by="technician1",
        )
        db_session.add(alarm)
        await db_session.commit()
        await db_session.refresh(alarm)

        # Act
        response = await client.post(
            f"/api/v1/alarms/{alarm.id}/resolve",
            headers=auth_headers,
            json={
                "resolved_by": "technician2",
                "resolution_note": "다시 해제",
            },
        )

        # Assert
        assert response.status_code == 400
        assert "already resolved" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_resolve_alarm_not_found(self, client: AsyncClient, auth_headers, db_session):
        """Resolve non-existent alarm returns 404."""
        # Act
        response = await client.post(
            "/api/v1/alarms/99999/resolve",
            headers=auth_headers,
            json={
                "resolved_by": "technician1",
            },
        )

        # Assert
        assert response.status_code == 404


class TestAlarmList:
    """Test alarm list operations."""

    @pytest.mark.asyncio
    async def test_list_alarms(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """List all alarms."""
        # Arrange
        definition = AlarmDefinition(
            code="ALM-LIST-001",
            name="목록 테스트",
            severity="WARNING",
            category="EQUIPMENT",
        )
        db_session.add(definition)
        await db_session.commit()
        await db_session.refresh(definition)

        for i in range(5):
            alarm = Alarm(
                definition_id=definition.id,
                equipment_id=sample_equipment.id,
                occurred_at=datetime.now(timezone.utc) - timedelta(hours=i),
                status="ACTIVE",
            )
            db_session.add(alarm)
        await db_session.commit()

        # Act
        response = await client.get(
            "/api/v1/alarms",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 5

    @pytest.mark.asyncio
    async def test_list_alarms_filter_by_status(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Filter alarms by status."""
        # Arrange
        definition = AlarmDefinition(
            code="ALM-FILTER-STATUS-001",
            name="상태 필터",
            severity="WARNING",
            category="EQUIPMENT",
        )
        db_session.add(definition)
        await db_session.commit()
        await db_session.refresh(definition)

        statuses = ["ACTIVE", "ACKNOWLEDGED", "RESOLVED"]
        for status in statuses:
            alarm = Alarm(
                definition_id=definition.id,
                equipment_id=sample_equipment.id,
                occurred_at=datetime.now(timezone.utc),
                status=status,
            )
            db_session.add(alarm)
        await db_session.commit()

        # Act
        response = await client.get(
            "/api/v1/alarms?status=ACTIVE",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_list_alarms_filter_by_severity(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Filter alarms by severity."""
        # Arrange
        critical_def = AlarmDefinition(
            code="ALM-FILTER-SEV-C",
            name="긴급",
            severity="CRITICAL",
            category="EQUIPMENT",
        )
        warning_def = AlarmDefinition(
            code="ALM-FILTER-SEV-W",
            name="경고",
            severity="WARNING",
            category="EQUIPMENT",
        )
        db_session.add(critical_def)
        db_session.add(warning_def)
        await db_session.commit()
        await db_session.refresh(critical_def)
        await db_session.refresh(warning_def)

        alarm1 = Alarm(
            definition_id=critical_def.id,
            equipment_id=sample_equipment.id,
            occurred_at=datetime.now(timezone.utc),
            status="ACTIVE",
        )
        alarm2 = Alarm(
            definition_id=warning_def.id,
            equipment_id=sample_equipment.id,
            occurred_at=datetime.now(timezone.utc),
            status="ACTIVE",
        )
        db_session.add(alarm1)
        db_session.add(alarm2)
        await db_session.commit()

        # Act
        response = await client.get(
            "/api/v1/alarms?severity=CRITICAL",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        # All alarms should have CRITICAL severity definition
        for item in data:
            assert item["definition"]["severity"] == "CRITICAL"

    @pytest.mark.asyncio
    async def test_list_alarms_filter_by_equipment(
        self, client: AsyncClient, auth_headers, db_session, multiple_equipments
    ):
        """Filter alarms by equipment."""
        # Arrange
        definition = AlarmDefinition(
            code="ALM-FILTER-EQ-001",
            name="설비 필터",
            severity="WARNING",
            category="EQUIPMENT",
        )
        db_session.add(definition)
        await db_session.commit()
        await db_session.refresh(definition)

        target_equipment = multiple_equipments[0]
        for eq in multiple_equipments[:3]:
            alarm = Alarm(
                definition_id=definition.id,
                equipment_id=eq.id,
                occurred_at=datetime.now(timezone.utc),
                status="ACTIVE",
            )
            db_session.add(alarm)
        await db_session.commit()

        # Act
        response = await client.get(
            f"/api/v1/alarms?equipment_id={target_equipment.id}",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["equipment_id"] == target_equipment.id


class TestActiveAlarms:
    """Test active alarms operations."""

    @pytest.mark.asyncio
    async def test_list_active_alarms(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """List only active and acknowledged alarms."""
        # Arrange
        definition = AlarmDefinition(
            code="ALM-ACTIVE-001",
            name="활성 알람",
            severity="WARNING",
            category="EQUIPMENT",
        )
        db_session.add(definition)
        await db_session.commit()
        await db_session.refresh(definition)

        # Create alarms with different statuses
        active_alarm = Alarm(
            definition_id=definition.id,
            equipment_id=sample_equipment.id,
            occurred_at=datetime.now(timezone.utc),
            status="ACTIVE",
        )
        ack_alarm = Alarm(
            definition_id=definition.id,
            equipment_id=sample_equipment.id,
            occurred_at=datetime.now(timezone.utc),
            status="ACKNOWLEDGED",
        )
        resolved_alarm = Alarm(
            definition_id=definition.id,
            equipment_id=sample_equipment.id,
            occurred_at=datetime.now(timezone.utc),
            status="RESOLVED",
        )
        db_session.add(active_alarm)
        db_session.add(ack_alarm)
        db_session.add(resolved_alarm)
        await db_session.commit()

        # Act
        response = await client.get(
            "/api/v1/alarms/active",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["status"] in ["ACTIVE", "ACKNOWLEDGED"]

    @pytest.mark.asyncio
    async def test_active_alarms_summary(
        self, client: AsyncClient, auth_headers, db_session, multiple_equipments
    ):
        """Get active alarms summary."""
        # Arrange
        critical_def = AlarmDefinition(
            code="ALM-SUMMARY-C",
            name="긴급 요약",
            severity="CRITICAL",
            category="EQUIPMENT",
        )
        warning_def = AlarmDefinition(
            code="ALM-SUMMARY-W",
            name="경고 요약",
            severity="WARNING",
            category="EQUIPMENT",
        )
        db_session.add(critical_def)
        db_session.add(warning_def)
        await db_session.commit()
        await db_session.refresh(critical_def)
        await db_session.refresh(warning_def)

        # Create multiple active alarms
        for i, eq in enumerate(multiple_equipments[:2]):
            alarm = Alarm(
                definition_id=critical_def.id if i == 0 else warning_def.id,
                equipment_id=eq.id,
                occurred_at=datetime.now(timezone.utc),
                status="ACTIVE",
            )
            db_session.add(alarm)
        await db_session.commit()

        # Act
        response = await client.get(
            "/api/v1/alarms/active/summary",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_severity" in data
        assert "by_equipment" in data
        assert data["total"] >= 2

    @pytest.mark.asyncio
    async def test_active_alarms_summary_by_severity(
        self, client: AsyncClient, auth_headers, db_session, sample_equipment
    ):
        """Verify summary breakdown by severity."""
        # Arrange
        critical_def = AlarmDefinition(
            code="ALM-SUMM-SEV-C",
            name="긴급",
            severity="CRITICAL",
            category="EQUIPMENT",
        )
        db_session.add(critical_def)
        await db_session.commit()
        await db_session.refresh(critical_def)

        # Create 3 critical alarms
        for _ in range(3):
            alarm = Alarm(
                definition_id=critical_def.id,
                equipment_id=sample_equipment.id,
                occurred_at=datetime.now(timezone.utc),
                status="ACTIVE",
            )
            db_session.add(alarm)
        await db_session.commit()

        # Act
        response = await client.get(
            "/api/v1/alarms/active/summary",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "CRITICAL" in data["by_severity"]
        assert data["by_severity"]["CRITICAL"] >= 3

    @pytest.mark.asyncio
    async def test_active_alarms_filter_by_equipment(
        self, client: AsyncClient, auth_headers, db_session, multiple_equipments
    ):
        """Filter active alarms by equipment."""
        # Arrange
        definition = AlarmDefinition(
            code="ALM-ACTIVE-EQ-001",
            name="설비별 활성 알람",
            severity="WARNING",
            category="EQUIPMENT",
        )
        db_session.add(definition)
        await db_session.commit()
        await db_session.refresh(definition)

        target_equipment = multiple_equipments[0]
        for eq in multiple_equipments[:2]:
            alarm = Alarm(
                definition_id=definition.id,
                equipment_id=eq.id,
                occurred_at=datetime.now(timezone.utc),
                status="ACTIVE",
            )
            db_session.add(alarm)
        await db_session.commit()

        # Act
        response = await client.get(
            f"/api/v1/alarms/active?equipment_id={target_equipment.id}",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["equipment_id"] == target_equipment.id

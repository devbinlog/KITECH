"""Cell membership remains atomic, explicit and visible through existing models."""

import pytest
from sqlalchemy import select

from src.app.models.equipment import Equipment
from src.app.models.master import Cell


@pytest.fixture
async def membership(db_session):
    first = Cell(code="CELL-A", name="First")
    second = Cell(code="CELL-B", name="Second")
    db_session.add_all([first, second])
    await db_session.flush()
    equipment = Equipment(eq_code="EQ-TEST", eq_name="Machine", equipment_type="CNC")
    db_session.add(equipment)
    await db_session.commit()
    return first, second, equipment


async def test_assign_move_unassign(client, admin_auth_headers, membership, db_session):
    first, second, equipment = membership
    previous = None
    for target in [first.id, second.id, None]:
        response = await client.patch(
            f"/api/v1/masters/equipments/{equipment.id}/cell",
            json={"cell_id": target, "expected_cell_id": previous},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200, response.text
        assert response.json()["cell_id"] == target
        assert await db_session.scalar(select(Equipment.cell_id).where(Equipment.id == equipment.id)) == target
        previous = target


async def test_stale_assignment_rejected(client, admin_auth_headers, membership):
    first, second, equipment = membership
    first_id = first.id
    url = f"/api/v1/masters/equipments/{equipment.id}/cell"
    assert (await client.patch(url, json={"cell_id": first.id, "expected_cell_id": None}, headers=admin_auth_headers)).status_code == 200
    response = await client.patch(url, json={"cell_id": second.id, "expected_cell_id": None}, headers=admin_auth_headers)
    assert response.status_code == 409
    current = await client.get(url.removesuffix("/cell"), headers=admin_auth_headers)
    assert current.json()["cell_id"] == first_id


async def test_invalid_cell_and_permission(client, admin_auth_headers, auth_headers, membership):
    first, _, equipment = membership
    url = f"/api/v1/masters/equipments/{equipment.id}/cell"
    assert (await client.patch(url, json={"cell_id": first.id, "expected_cell_id": None}, headers=auth_headers)).status_code == 403
    assert (await client.patch(url, json={"cell_id": 99999, "expected_cell_id": None}, headers=admin_auth_headers)).status_code == 404
    assert (await client.patch(url, json={"cell_id": first.id}, headers=admin_auth_headers)).status_code == 422


async def test_deleted_equipment_can_only_be_unassigned(client, admin_auth_headers, membership, db_session):
    first, second, equipment = membership
    equipment.cell_id = first.id
    equipment.is_deleted = True
    await db_session.commit()
    url = f"/api/v1/masters/equipments/{equipment.id}/cell"
    assert (await client.delete(f"/api/v1/masters/cells/{first.id}", headers=admin_auth_headers)).status_code == 409
    assert (await client.patch(url, json={"cell_id": second.id, "expected_cell_id": first.id}, headers=admin_auth_headers)).status_code == 404
    assert (await client.patch(url, json={"cell_id": None, "expected_cell_id": first.id}, headers=admin_auth_headers)).status_code == 200
    assert (await client.delete(f"/api/v1/masters/cells/{first.id}", headers=admin_auth_headers)).status_code == 204


async def test_update_cell_and_duplicate_code(client, admin_auth_headers, membership):
    first, second, _ = membership
    url = f"/api/v1/masters/cells/{first.id}"
    data = {"code": "CELL-EDIT", "name": "Updated", "location": "Building A"}
    response = await client.put(url, json=data, headers=admin_auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"
    response = await client.put(url, json={**data, "code": second.code}, headers=admin_auth_headers)
    assert response.status_code == 409


async def test_cannot_delete_occupied_cell(client, admin_auth_headers, membership):
    first, _, equipment = membership
    await client.patch(f"/api/v1/masters/equipments/{equipment.id}/cell", json={"cell_id": first.id, "expected_cell_id": None}, headers=admin_auth_headers)
    response = await client.delete(f"/api/v1/masters/cells/{first.id}", headers=admin_auth_headers)
    assert response.status_code == 409

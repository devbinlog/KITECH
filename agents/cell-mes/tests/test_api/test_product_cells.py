"""Allowed cells are product-level, validated and independent of routing saves."""

import pytest
from sqlalchemy import select

from src.app.models.master import Cell, ProductCell


@pytest.fixture
async def cells(db_session):
    values = [Cell(code="A", name="Cell A"), Cell(code="B", name="Cell B")]
    db_session.add_all(values)
    await db_session.commit()
    return values


async def test_save_replace_clear_and_routing_independence(client, auth_headers, sample_product, cells, db_session):
    url = f"/api/v1/masters/products/{sample_product.id}/cells"
    assert (await client.get(url, headers=auth_headers)).json()["cell_ids"] == []
    ids = [c.id for c in cells]
    for selection in [ids, ids, ids[1:], []]:
        response = await client.put(url, headers=auth_headers, json={"cell_ids": selection})
        assert response.status_code == 200, response.text
        assert response.json() == {"product_id": sample_product.id, "cell_ids": selection}
        await client.put(url.replace("/cells", "/routings"), headers=auth_headers, json=[])
        assert (await client.get(url, headers=auth_headers)).json()["cell_ids"] == selection
        assert list((await db_session.scalars(select(ProductCell.cell_id).order_by(ProductCell.cell_id))).all()) == selection


@pytest.mark.parametrize("value,status", [([999999], 400), ([1, 1], 422), ([-1], 422), ([True], 422)])
async def test_invalid_cells_do_not_erase_existing(client, auth_headers, sample_product, cells, value, status):
    url = f"/api/v1/masters/products/{sample_product.id}/cells"
    await client.put(url, headers=auth_headers, json={"cell_ids": [cells[0].id]})
    assert (await client.put(url, headers=auth_headers, json={"cell_ids": value})).status_code == status
    assert (await client.get(url, headers=auth_headers)).json()["cell_ids"] == [cells[0].id]


async def test_auth_and_missing_product(client, auth_headers, sample_product, db_session):
    url = f"/api/v1/masters/products/{sample_product.id}/cells"
    assert (await client.get(url)).status_code == 401
    assert (await client.put(url, json={"cell_ids": []})).status_code == 401
    sample_product.is_deleted = True
    await db_session.commit()
    for product_id in [sample_product.id, 999999]:
        url = f"/api/v1/masters/products/{product_id}/cells"
        assert (await client.get(url, headers=auth_headers)).status_code == 404
        assert (await client.put(url, headers=auth_headers, json={"cell_ids": []})).status_code == 404


async def test_linked_cell_cannot_be_deleted(client, auth_headers, admin_auth_headers, sample_product, cells):
    url = f"/api/v1/masters/products/{sample_product.id}/cells"
    await client.put(url, headers=auth_headers, json={"cell_ids": [cells[0].id]})
    cell_url = f"/api/v1/masters/cells/{cells[0].id}"
    assert (await client.delete(cell_url, headers=admin_auth_headers)).status_code == 409
    await client.put(url, headers=auth_headers, json={"cell_ids": []})
    assert (await client.delete(cell_url, headers=admin_auth_headers)).status_code == 204

"""Seconds, explicit inheritance, and scheduler projection use the same rules."""

import pytest

from src.app.models.master import ProcessRouting
from src.app.services.scheduling.projector import SchedulerProjector


@pytest.mark.parametrize("override,standard,expected", [(123, 60, 123), (0, 60, 0), (None, 75, 75), (None, 0, 0)])
async def test_override_clear_and_projection(
    client, auth_headers, sample_product, sample_std_process, db_session, override, standard, expected
):
    sample_std_process.cycle_time_sec = standard
    db_session.add(ProcessRouting(product_id=sample_product.id, std_process_id=sample_std_process.id,
                                 sequence=10, revision="B", cycle_time_sec=417,
                                 cycle_time_breakdown={"source": "old-analysis"}))
    await db_session.commit()
    response = await client.put(f"/api/v1/masters/products/{sample_product.id}/routings",
                                headers=auth_headers, json=[{
                                    "std_process_id": sample_std_process.id, "sequence": 10,
                                    "revision": "B", "cycle_time_sec": override,
                                }])
    assert response.status_code == 200, response.text
    assert response.json()[0]["cycle_time_sec"] == override
    assert response.json()[0]["cycle_time_breakdown"] is None
    assert response.json()[0]["revision"] == "B"
    operations = await SchedulerProjector(db_session).get_routing_operations(sample_product.id)
    assert operations[0]["cycle_time_sec"] == expected
    assert operations[0]["nc_code"]["cycle_time_sec"] == expected
    if override is None:
        sample_std_process.cycle_time_sec = 91
        await db_session.commit()
        operations = await SchedulerProjector(db_session).get_routing_operations(sample_product.id)
        assert operations[0]["cycle_time_sec"] == 91


@pytest.mark.parametrize("value", [-1, 1.5, 2147483648])
async def test_invalid_seconds(client, auth_headers, sample_product, sample_std_process, value):
    response = await client.put(f"/api/v1/masters/products/{sample_product.id}/routings",
                                headers=auth_headers, json=[{
                                    "std_process_id": sample_std_process.id, "sequence": 10,
                                    "cycle_time_sec": value,
                                }])
    assert response.status_code == 422

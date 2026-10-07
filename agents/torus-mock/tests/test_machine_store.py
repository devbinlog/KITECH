"""TDD tests for Machine Store."""

from pathlib import Path

import pytest

from src.app.services.machine_store import MachineStore, reset_store


DATA_DIR = Path(__file__).parent.parent / "data"


@pytest.fixture
def store() -> MachineStore:
    """Create a fresh store with default data."""
    reset_store()
    s = MachineStore()
    s.load_from_json(DATA_DIR / "default_machines.json")
    return s


class TestLoadFromJson:
    """Test loading machine data from JSON."""

    def test_load_two_machines(self, store):
        assert len(store.machines) == 2
        assert 1 in store.machines
        assert 2 in store.machines

    def test_machine_1_is_fanuc(self, store):
        m = store.machines[1]
        assert m.machineName == "FANUC-Mill-01"
        assert m.vendorId == 1
        assert m.vendorName == "FANUC"
        assert m.modelName == "0i-MF"

    def test_machine_2_is_siemens(self, store):
        m = store.machines[2]
        assert m.machineName == "SIEMENS-Mill-01"
        assert m.vendorId == 2
        assert m.vendorName == "SIEMENS"
        assert m.modelName == "840D sl"

    def test_machine_1_axes(self, store):
        m = store.machines[1]
        assert len(m.channel) == 1
        assert len(m.channel[0].axis) == 3
        assert m.channel[0].axis[0].axisName == "X"
        assert m.channel[0].axis[1].axisName == "Y"
        assert m.channel[0].axis[2].axisName == "Z"

    def test_machine_2_has_5_axes(self, store):
        m = store.machines[2]
        assert len(m.channel[0].axis) == 5
        assert m.channel[0].axis[3].axisName == "A"
        assert m.channel[0].axis[4].axisName == "C"

    def test_machine_2_has_2_channels(self, store):
        m = store.machines[2]
        assert len(m.channel) == 2


class TestListMachines:
    """Test machine listing."""

    def test_list_returns_all(self, store):
        result = store.list_machines()
        assert len(result) == 2

    def test_list_summary_fields(self, store):
        result = store.list_machines()
        m1 = next(m for m in result if m["machineId"] == 1)
        assert m1["machineName"] == "FANUC-Mill-01"
        assert m1["vendorName"] == "FANUC"
        assert m1["channels"] == 1


class TestGetValue:
    """Test getData via store."""

    def test_get_axis_position(self, store):
        resp = store.get_value(
            "data://machine/channel/axis/machinePosition",
            "machine=1&channel=1&axis=1",
        )
        assert resp.success
        assert resp.value == 0.0  # default initial

    def test_get_multiple_axes(self, store):
        resp = store.get_value(
            "data://machine/channel/axis/axisName",
            "machine=1&channel=1&axis=1-3",
        )
        assert resp.success
        assert resp.value == ["X", "Y", "Z"]

    def test_get_spindle_limit(self, store):
        resp = store.get_value(
            "data://machine/channel/spindle/spindleLimit",
            "machine=1&channel=1&spindle=1",
        )
        assert resp.success
        assert resp.value == 12000.0

    def test_get_nc_memory(self, store):
        resp = store.get_value(
            "data://machine/ncMemory/totalCapacity",
            "machine=1",
        )
        assert resp.success
        assert resp.value == 2097152.0

    def test_get_nonexistent_machine(self, store):
        resp = store.get_value(
            "data://machine/channel/axis/machinePosition",
            "machine=99&channel=1&axis=1",
        )
        assert not resp.success
        assert "not found" in resp.error.lower()


class TestSetValue:
    """Test updateData via store."""

    def test_set_axis_limit(self, store):
        resp = store.set_value(
            "data://machine/channel/axis/axisLimitPlus",
            "machine=1&channel=1&axis=1",
            600.0,
        )
        assert resp.success
        assert resp.value == 600.0

        # Verify it was saved
        verify = store.get_value(
            "data://machine/channel/axis/axisLimitPlus",
            "machine=1&channel=1&axis=1",
        )
        assert verify.value == 600.0

    def test_set_read_only_field_fails(self, store):
        resp = store.set_value(
            "data://machine/channel/axis/machinePosition",
            "machine=1&channel=1&axis=1",
            999.0,
        )
        assert not resp.success
        assert "read-only" in resp.error.lower()

    def test_set_work_counter(self, store):
        resp = store.set_value(
            "data://machine/channel/workStatus/workCounter/currentWorkCounter",
            "machine=1&channel=1&workStatus=1",
            42,
        )
        assert resp.success
        assert resp.value == 42

    def test_set_user_variable(self, store):
        resp = store.set_value(
            "data://machine/channel/variable/userVariable",
            "machine=1&channel=1&variable=1",
            3.14,
        )
        assert resp.success


class TestPlcOperations:
    """Test PLC get/set."""

    def test_read_rbit_block(self, store):
        resp = store.get_plc(machine_id=1, plc_type=1, start_address=0, count=4)
        assert resp.success
        assert len(resp.data) == 4
        assert resp.data[2] is True  # 3rd bit is true in default data

    def test_write_bit_block(self, store):
        resp = store.set_plc(machine_id=1, plc_type=2, start_address=0, data=[True, True, False])
        assert resp.success

        # Verify
        verify = store.get_plc(machine_id=1, plc_type=2, start_address=0, count=3)
        assert verify.data == [True, True, False]

    def test_write_readonly_plc_fails(self, store):
        resp = store.set_plc(machine_id=1, plc_type=1, start_address=0, data=[True])
        assert not resp.success
        assert "read-only" in resp.error.lower()

    def test_write_word_block(self, store):
        resp = store.set_plc(machine_id=1, plc_type=6, start_address=0, data=[1000, 2000, 3000])
        assert resp.success

        verify = store.get_plc(machine_id=1, plc_type=6, start_address=0, count=3)
        assert verify.data == [1000, 2000, 3000]

    def test_plc_nonexistent_machine(self, store):
        resp = store.get_plc(machine_id=99, plc_type=1, start_address=0, count=1)
        assert not resp.success

"""TDD tests for TORUS URI address parser."""

import pytest

from src.app.schemas import MachineData, Channel, Axis, Spindle, Feed, WorkStatus
from src.app.services.address_parser import (
    parse_address,
    parse_filter_value,
    resolve_value,
)


class TestParseFilterValue:
    """Test filter value parsing."""

    def test_single_value(self):
        assert parse_filter_value("1") == [1]

    def test_range(self):
        assert parse_filter_value("1-3") == [1, 2, 3]

    def test_comma_separated(self):
        assert parse_filter_value("1,3,5") == [1, 3, 5]

    def test_single_large(self):
        assert parse_filter_value("100") == [100]

    def test_range_same(self):
        assert parse_filter_value("3-3") == [3]


class TestParseAddress:
    """Test address parsing."""

    def test_basic_address(self):
        result = parse_address(
            "data://machine/channel/axis/machinePosition",
            "machine=1&channel=1&axis=1",
        )
        assert result.path_segments == ["channel", "axis", "machinePosition"]
        assert result.filters == {"machine": [1], "channel": [1], "axis": [1]}
        assert result.leaf == "machinePosition"

    def test_no_filter(self):
        result = parse_address("data://machine/channel")
        assert result.path_segments == ["channel"]
        assert result.filters == {}

    def test_empty_address(self):
        result = parse_address("data://machine", "machine=1")
        assert result.path_segments == []
        assert result.filters == {"machine": [1]}

    def test_spindle_address(self):
        result = parse_address(
            "data://machine/channel/spindle/rpm/actualSpeed",
            "machine=1&channel=1&spindle=1",
        )
        assert result.path_segments == ["channel", "spindle", "rpm", "actualSpeed"]
        assert result.filters["spindle"] == [1]

    def test_plc_address(self):
        result = parse_address("data://machine/plc/bitBlock", "machine=1")
        assert result.path_segments == ["plc", "bitBlock"]

    def test_range_filter(self):
        result = parse_address(
            "data://machine/channel/axis/machinePosition",
            "machine=1&channel=1&axis=1-3",
        )
        assert result.filters["axis"] == [1, 2, 3]

    def test_ncMemory_address(self):
        result = parse_address("data://machine/ncMemory/totalCapacity", "machine=1")
        assert result.path_segments == ["ncMemory", "totalCapacity"]

    def test_feed_address(self):
        result = parse_address(
            "data://machine/channel/feed/feedRate/commandedSpeed",
            "machine=1&channel=1",
        )
        assert result.path_segments == ["channel", "feed", "feedRate", "commandedSpeed"]


class TestResolveValue:
    """Test value resolution from MachineData."""

    @pytest.fixture
    def machine(self):
        """Create a simple machine for testing."""
        return MachineData(
            machineId=1,
            machineName="Test",
            vendorId=1,
            vendorName="FANUC",
            modelName="Test-01",
            channel=[
                Channel(
                    ncState=2,
                    numberOfAxes=3,
                    numberOfSpindles=1,
                    axis=[
                        Axis(axisName="X", machinePosition=100.5, workPosition=50.0),
                        Axis(axisName="Y", machinePosition=200.3, workPosition=150.0),
                        Axis(axisName="Z", machinePosition=-50.0, workPosition=-100.0),
                    ],
                    spindle=[
                        Spindle(spindleLoad=45.0),
                    ],
                    feed=Feed(feedOverride=80.0),
                    workStatus=[WorkStatus()],
                )
            ],
        )

    def test_resolve_axis_position(self, machine):
        parsed = parse_address(
            "data://machine/channel/axis/machinePosition",
            "machine=1&channel=1&axis=1",
        )
        results = resolve_value(machine, parsed)
        assert len(results) == 1
        assert results[0].success
        assert results[0].value == 100.5

    def test_resolve_multiple_axes(self, machine):
        parsed = parse_address(
            "data://machine/channel/axis/machinePosition",
            "machine=1&channel=1&axis=1-3",
        )
        results = resolve_value(machine, parsed)
        assert len(results) == 3
        assert results[0].value == 100.5
        assert results[1].value == 200.3
        assert results[2].value == -50.0

    def test_resolve_spindle(self, machine):
        parsed = parse_address(
            "data://machine/channel/spindle/spindleLoad",
            "machine=1&channel=1&spindle=1",
        )
        results = resolve_value(machine, parsed)
        assert len(results) == 1
        assert results[0].value == 45.0

    def test_resolve_feed_override(self, machine):
        parsed = parse_address(
            "data://machine/channel/feed/feedOverride",
            "machine=1&channel=1",
        )
        results = resolve_value(machine, parsed)
        assert len(results) == 1
        assert results[0].value == 80.0

    def test_resolve_channel_state(self, machine):
        parsed = parse_address(
            "data://machine/channel/ncState",
            "machine=1&channel=1",
        )
        results = resolve_value(machine, parsed)
        assert len(results) == 1
        assert results[0].value == 2

    def test_resolve_entire_machine(self, machine):
        parsed = parse_address("data://machine", "machine=1")
        results = resolve_value(machine, parsed)
        assert len(results) == 1
        assert results[0].success
        assert isinstance(results[0].value, dict)
        assert results[0].value["machineName"] == "Test"

    def test_resolve_axis_object(self, machine):
        parsed = parse_address(
            "data://machine/channel/axis",
            "machine=1&channel=1&axis=1",
        )
        results = resolve_value(machine, parsed)
        assert len(results) == 1
        assert results[0].success
        assert isinstance(results[0].value, dict)
        assert results[0].value["axisName"] == "X"

    def test_resolve_invalid_path(self, machine):
        parsed = parse_address(
            "data://machine/channel/nonexistent",
            "machine=1&channel=1",
        )
        results = resolve_value(machine, parsed)
        assert len(results) == 1
        assert not results[0].success
        assert "not found" in results[0].error.lower()

    def test_resolve_axis_out_of_range(self, machine):
        parsed = parse_address(
            "data://machine/channel/axis/machinePosition",
            "machine=1&channel=1&axis=99",
        )
        results = resolve_value(machine, parsed)
        assert len(results) == 1
        assert not results[0].success

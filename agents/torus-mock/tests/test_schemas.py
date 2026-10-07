"""Tests for TORUS Pydantic schemas."""

import json

from src.app.schemas import (
    Axis,
    AxisPower,
    Channel,
    Feed,
    MachineData,
    Spindle,
    SpindleRpm,
    WorkCounter,
    WorkStatus,
    ActiveTool,
    ToolEdge,
    PlcData,
    NcMemory,
    WRITABLE_FIELDS,
    PLC_WRITABLE_TYPES,
)


class TestAxisSchema:
    """Test Axis model."""

    def test_default_creation(self):
        axis = Axis()
        assert axis.machinePosition == 0.0
        assert axis.axisName == ""
        assert axis.axisEnabled is True
        assert axis.axisTemperature == 25.0

    def test_with_values(self):
        axis = Axis(
            axisName="X",
            machinePosition=100.5,
            axisLimitPlus=500.0,
            axisLimitMinus=-500.0,
        )
        assert axis.axisName == "X"
        assert axis.machinePosition == 100.5
        assert axis.axisLimitPlus == 500.0

    def test_axis_power_embedded(self):
        axis = Axis()
        assert isinstance(axis.axisPower, AxisPower)
        assert axis.axisPower.actualPowerConsumption == 0.0

    def test_json_roundtrip(self):
        axis = Axis(axisName="Y", machinePosition=55.3)
        data = json.loads(axis.model_dump_json())
        restored = Axis(**data)
        assert restored.axisName == "Y"
        assert restored.machinePosition == 55.3


class TestSpindleSchema:
    """Test Spindle model."""

    def test_default(self):
        sp = Spindle()
        assert sp.spindleLoad == 0.0
        assert sp.spindleLimit == 12000.0
        assert isinstance(sp.rpm, SpindleRpm)

    def test_rpm_values(self):
        sp = Spindle(rpm=SpindleRpm(commandedSpeed=3000, actualSpeed=2998))
        assert sp.rpm.commandedSpeed == 3000
        assert sp.rpm.actualSpeed == 2998


class TestChannelSchema:
    """Test Channel model."""

    def test_default(self):
        ch = Channel()
        assert ch.ncState == 0
        assert ch.axis == []
        assert ch.spindle == []
        assert isinstance(ch.feed, Feed)

    def test_with_axes(self):
        ch = Channel(
            numberOfAxes=2,
            axis=[Axis(axisName="X"), Axis(axisName="Y")],
        )
        assert len(ch.axis) == 2
        assert ch.axis[0].axisName == "X"


class TestMachineDataSchema:
    """Test top-level MachineData model."""

    def test_default(self):
        m = MachineData()
        assert m.machineId == 1
        assert m.vendorId == 1
        assert m.channel == []
        assert isinstance(m.plc, PlcData)
        assert isinstance(m.ncMemory, NcMemory)

    def test_full_creation(self):
        m = MachineData(
            machineId=1,
            machineName="Test CNC",
            vendorId=1,
            vendorName="FANUC",
            channel=[
                Channel(
                    ncState=2,
                    numberOfAxes=3,
                    axis=[Axis(axisName=n) for n in ["X", "Y", "Z"]],
                    spindle=[Spindle(spindleLimit=10000)],
                )
            ],
        )
        assert m.machineName == "Test CNC"
        assert len(m.channel) == 1
        assert len(m.channel[0].axis) == 3

    def test_json_roundtrip(self):
        m = MachineData(
            machineId=2,
            machineName="SIEMENS Test",
            vendorId=2,
            vendorName="SIEMENS",
        )
        data = json.loads(m.model_dump_json())
        restored = MachineData(**data)
        assert restored.machineId == 2
        assert restored.vendorName == "SIEMENS"


class TestWorkStatusSchema:
    """Test WorkStatus model."""

    def test_default_counter(self):
        ws = WorkStatus()
        assert ws.workCounter.currentWorkCounter == 0
        assert ws.workCounter.targetWorkCounter == 0
        assert ws.machiningTime.processingMachiningTime == 0.0

    def test_counter_values(self):
        wc = WorkCounter(currentWorkCounter=5, targetWorkCounter=100, totalWorkCounter=1000)
        assert wc.currentWorkCounter == 5
        assert wc.totalWorkCounter == 1000


class TestActiveToolSchema:
    """Test ActiveTool model."""

    def test_default(self):
        at = ActiveTool()
        assert at.toolNumber == 0
        assert at.toolEdge == []

    def test_with_edge(self):
        at = ActiveTool(
            toolNumber=1,
            toolName="T01",
            toolEdge=[ToolEdge(edgeNumber=1, geoLengthOffset=100.0)],
        )
        assert at.toolEdge[0].geoLengthOffset == 100.0


class TestPlcDataSchema:
    """Test PlcData model."""

    def test_default(self):
        plc = PlcData()
        assert plc.bitBlock == []
        assert plc.rbitBlock == []

    def test_with_data(self):
        plc = PlcData(
            bitBlock=[True, False, True],
            wordBlock=[1000, 2000],
        )
        assert plc.bitBlock[0] is True
        assert plc.wordBlock[1] == 2000


class TestWritableFields:
    """Test WRITABLE_FIELDS and PLC_WRITABLE_TYPES constants."""

    def test_axis_limits_writable(self):
        assert "axisLimitPlus" in WRITABLE_FIELDS
        assert "axisLimitMinus" in WRITABLE_FIELDS

    def test_machine_position_not_writable(self):
        assert "machinePosition" not in WRITABLE_FIELDS

    def test_plc_writable_types(self):
        assert PLC_WRITABLE_TYPES == {2, 4, 6, 8, 10}

    def test_control_options_writable(self):
        assert "singleBlock" in WRITABLE_FIELDS
        assert "dryRun" in WRITABLE_FIELDS
        assert "machineLock" in WRITABLE_FIELDS

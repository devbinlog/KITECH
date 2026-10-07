"""TORUS Platform Machine Data Model — Pydantic schemas.

Maps the hierarchical CNC data model from TORUS Platform User Manual Section 5.
Each field is annotated with R (read-only) or R/W (read-write) access.

Hierarchy:
  MachineData
  ├── channels[] → Channel
  │   ├── axes[] → Axis (axisPower)
  │   ├── spindles[] → Spindle (rpm, spindlePower)
  │   ├── feed → Feed (feedRate)
  │   ├── workStatuses[] → WorkStatus (workCounter, machiningTime)
  │   ├── activeTool → ActiveTool (toolEdge → toolLife)
  │   ├── currentProgram → CurrentProgram (controlOption, modal, currentFile, mainFile)
  │   ├── alarms[] → Alarm
  │   ├── variables[] → Variable
  │   └── workOffsets[] → WorkOffset
  ├── plc → PlcData (PlcMemory blocks)
  ├── ncMemory → NcMemory
  ├── toolArea → ToolArea (magazines[], tools[])
  └── buffer → Buffer (streams[])
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── Axis ────────────────────────────────────────────────────────────────────


class AxisPower(BaseModel):
    """Axis power consumption. All R."""

    actualPowerConsumption: float = 0.0  # R
    powerConsumption: float = 0.0  # R
    regeneratedPower: float = 0.0  # R


class Axis(BaseModel):
    """Single axis within a channel."""

    # Positions — R
    machinePosition: float = 0.0  # R
    workPosition: float = 0.0  # R
    distanceToGo: float = 0.0  # R
    relativePosition: float = 0.0  # R

    # Names — R
    axisName: str = ""  # R
    relativeAxisName: str = ""  # R

    # Load/Feed — R
    axisLoad: float = 0.0  # R
    axisFeed: float = 0.0  # R

    # Limits — R/W
    axisLimitPlus: float = 9999.0  # R/W
    axisLimitMinus: float = -9999.0  # R/W
    workAreaLimitPlus: float = 9999.0  # R/W
    workAreaLimitMinus: float = -9999.0  # R/W
    workAreaLimitPlusEnabled: bool = False  # R/W
    workAreaLimitMinusEnabled: bool = False  # R/W

    # Flags — R
    axisEnabled: bool = True  # R
    interlockEnabled: bool = False  # R
    constantSurfaceSpeedControlEnabled: bool = False  # R

    # Electrical — R
    axisCurrent: float = 0.0  # R
    machineOrigin: float = 0.0  # R/W
    axisTemperature: float = 25.0  # R

    # Power — R
    axisPower: AxisPower = Field(default_factory=AxisPower)  # R


# ─── Spindle ─────────────────────────────────────────────────────────────────


class SpindleRpm(BaseModel):
    """Spindle RPM info. All R."""

    commandedSpeed: float = 0.0  # R
    actualSpeed: float = 0.0  # R
    speedUnit: int = 0  # R (0=rpm)


class SpindlePower(BaseModel):
    """Spindle power consumption. All R."""

    actualPowerConsumption: float = 0.0  # R
    powerConsumption: float = 0.0  # R
    regeneratedPower: float = 0.0  # R


class Spindle(BaseModel):
    """Single spindle within a channel."""

    spindleLoad: float = 0.0  # R
    spindleOverride: float = 100.0  # R
    spindleLimit: float = 12000.0  # R
    spindleEnabled: bool = True  # R
    spindleCurrent: float = 0.0  # R
    spindleTemperature: float = 25.0  # R
    rpm: SpindleRpm = Field(default_factory=SpindleRpm)  # R
    spindlePower: SpindlePower = Field(default_factory=SpindlePower)  # R


# ─── Feed ────────────────────────────────────────────────────────────────────


class FeedRate(BaseModel):
    """Feed rate details. All R."""

    commandedSpeed: float = 0.0  # R
    actualSpeed: float = 0.0  # R
    speedUnit: int = 0  # R (0=mm/min)


class Feed(BaseModel):
    """Feed data per channel."""

    feedOverride: float = 100.0  # R
    rapidOverride: float = 100.0  # R
    feedRate: FeedRate = Field(default_factory=FeedRate)  # R


# ─── WorkStatus ──────────────────────────────────────────────────────────────


class WorkCounter(BaseModel):
    """Work piece counter."""

    currentWorkCounter: int = 0  # R/W
    targetWorkCounter: int = 0  # R/W
    totalWorkCounter: int = 0  # R


class MachiningTime(BaseModel):
    """Machining time tracking (seconds)."""

    processingMachiningTime: float = 0.0  # R
    estimatedMachiningTime: float = 0.0  # R (SIEMENS only)
    machineOperationTime: float = 0.0  # R
    actualCuttingTime: float = 0.0  # R


class WorkStatus(BaseModel):
    """Work status per channel."""

    workCounter: WorkCounter = Field(default_factory=WorkCounter)
    machiningTime: MachiningTime = Field(default_factory=MachiningTime)


# ─── ActiveTool ──────────────────────────────────────────────────────────────


class ToolLife(BaseModel):
    """Tool life info. All R."""

    maxToolLife: float = 0.0  # R
    restToolLife: float = 0.0  # R
    toolLifeCount: float = 0.0  # R
    toolLifeAlarm: float = 0.0  # R (SIEMENS only)


class ToolEdge(BaseModel):
    """Tool edge compensation data. All R."""

    edgeNumber: int = 1  # R
    toolType: int = 0  # R
    lengthOffsetNumber: int = 0  # R
    geoLengthOffset: float = 0.0  # R
    wearLengthOffset: float = 0.0  # R
    geoRadiusOffset: float = 0.0  # R
    wearRadiusOffset: float = 0.0  # R
    edgeEnabled: bool = True  # R
    geoLengthOffsetZ: float = 0.0  # R
    wearLengthOffsetZ: float = 0.0  # R
    geoLengthOffsetY: float = 0.0  # R
    wearLengthOffsetY: float = 0.0  # R
    geoOffsetNumber: int = 0  # R
    wearOffsetNumber: int = 0  # R
    cuttingEdgePosition: int = 0  # R
    tipAngle: float = 0.0  # R
    holderAngle: float = 0.0  # R (lathe)
    insertAngle: float = 0.0  # R (lathe)
    insertWidth: float = 0.0  # R (SIEMENS)
    insertLength: float = 0.0  # R (SIEMENS)
    referenceDirectionHolderAngle: float = 0.0  # R (SIEMENS)
    directionOfSpindleRotation: int = 0  # R (SIEMENS)
    numberOfTeeth: int = 0  # R (SIEMENS)
    toolLife: ToolLife = Field(default_factory=ToolLife)


class ActiveTool(BaseModel):
    """Active tool info per channel. All R."""

    locationNumber: int = 0  # R
    toolName: str = ""  # R
    toolNumber: int = 0  # R
    numberOfEdges: int = 1  # R
    toolEnabled: int = 1  # R
    magazineNumber: int = 1  # R
    sisterToolNumber: int = 0  # R
    toolLifeUnit: int = 0  # R
    toolGroupNumber: int = 0  # R
    toolUseOrderNumber: int = 0  # R
    toolStatus: int = 0  # R
    toolEdge: List[ToolEdge] = Field(default_factory=list)


# ─── CurrentProgram ──────────────────────────────────────────────────────────


class ModalCode(BaseModel):
    """Modal G-code info. R."""

    modalIndex: int = 0  # R
    modalCode: str = ""  # R


class ProgramFileInfo(BaseModel):
    """Program file info. R."""

    programName: str = ""  # R
    programPath: str = ""  # R
    programSize: float = 0.0  # R (bytes)
    programDate: str = ""  # R (yyyy-MM-ddTHH:mm:ss)
    programNameWithPath: str = ""  # R


class CurrentTotalWorkOffset(BaseModel):
    """Current total work offset (read-only). R."""

    workOffsetIndex: int = 0  # R
    workOffsetCode: str = ""  # R
    workOffsetValue: List[float] = Field(default_factory=list)  # R
    workOffsetRotation: List[float] = Field(default_factory=list)  # R (SIEMENS)
    workOffsetScalingFactor: List[float] = Field(default_factory=list)  # R (SIEMENS)
    workOffsetMirroringEnabled: List[bool] = Field(default_factory=list)  # R (SIEMENS)


class ControlOption(BaseModel):
    """Control options. R/W."""

    singleBlock: bool = False  # R/W
    dryRun: bool = False  # R/W
    optionalStop: bool = False  # R/W
    blockSkip: List[bool] = Field(default_factory=list)  # R/W
    machineLock: bool = False  # R/W


class CurrentProgram(BaseModel):
    """Current program info per channel."""

    sequenceNumber: int = 0  # R
    currentBlockCounter: int = 0  # R
    lastBlock: str = ""  # R
    currentBlock: str = ""  # R
    nextBlock: str = ""  # R
    activePartProgram: str = ""  # R (max 200 chars)
    programMode: int = 0  # R
    currentWorkOffsetIndex: int = 0  # R
    currentWorkOffsetCode: str = ""  # R
    currentDepthLevel: int = 0  # R (SIEMENS, MITSUBISHI)
    modal: List[ModalCode] = Field(default_factory=list)  # R
    currentTotalWorkOffset: CurrentTotalWorkOffset = Field(default_factory=CurrentTotalWorkOffset)
    currentFile: ProgramFileInfo = Field(default_factory=ProgramFileInfo)  # R
    mainFile: ProgramFileInfo = Field(default_factory=ProgramFileInfo)  # R
    controlOption: ControlOption = Field(default_factory=ControlOption)  # R/W


# ─── Alarm ───────────────────────────────────────────────────────────────────


class Alarm(BaseModel):
    """Alarm record. All R."""

    alarmText: str = ""  # R
    alarmCategory: str = ""  # R
    alarmNumber: str = ""  # R
    raisedTimeStamp: str = ""  # R


# ─── Variable ────────────────────────────────────────────────────────────────


class Variable(BaseModel):
    """NC variable. userVariable is R/W."""

    userVariable: float = 0.0  # R/W


# ─── WorkOffset ──────────────────────────────────────────────────────────────


class WorkOffset(BaseModel):
    """Work offset data per offset index. R/W fields."""

    workOffsetValue: List[float] = Field(default_factory=list)  # R/W
    workOffsetRotation: List[float] = Field(default_factory=list)  # R/W (SIEMENS)
    workOffsetScalingFactor: List[float] = Field(default_factory=list)  # R/W (SIEMENS)
    workOffsetMirroringEnabled: List[bool] = Field(default_factory=list)  # R/W (SIEMENS)
    workOffsetFine: List[float] = Field(default_factory=list)  # R/W (SIEMENS)


# ─── Channel ─────────────────────────────────────────────────────────────────


class Channel(BaseModel):
    """Channel: groups axes, spindles, programs, tools."""

    # State flags — R
    ncState: int = 0  # R (0=reset, 1=stop, 2=start, 3=hold)
    motionStatus: int = 0  # R
    emergencyStatus: int = 0  # R
    numberOfAxes: int = 0  # R
    numberOfSpindles: int = 0  # R
    alarmStatus: int = 0  # R
    numberOfAlarms: int = 0  # R
    operateMode: int = 0  # R (0=auto, 1=mdi, 2=jog, etc.)

    # Collections
    axis: List[Axis] = Field(default_factory=list)
    spindle: List[Spindle] = Field(default_factory=list)
    feed: Feed = Field(default_factory=Feed)
    workStatus: List[WorkStatus] = Field(default_factory=lambda: [WorkStatus()])
    activeTool: ActiveTool = Field(default_factory=ActiveTool)
    currentProgram: CurrentProgram = Field(default_factory=CurrentProgram)
    alarm: List[Alarm] = Field(default_factory=list)
    variable: List[Variable] = Field(default_factory=lambda: [Variable()])
    workOffset: List[WorkOffset] = Field(default_factory=list)


# ─── PLC ─────────────────────────────────────────────────────────────────────


class PlcMemory(BaseModel):
    """Single PLC memory block.

    Types: 1=rbitBlock(R), 2=bitBlock(R/W), 3=rbyteBlock(R), 4=byteBlock(R/W),
           5=rwordBlock(R), 6=wordBlock(R/W), 7=rdwordBlock(R), 8=dwordBlock(R/W),
           9=rqwordBlock(R), 10=qwordBlock(R/W)
    """

    type: int = 0
    startAddress: int = 0
    count: int = 0
    data: List[Any] = Field(default_factory=list)


class PlcData(BaseModel):
    """PLC data — contains memory blocks."""

    rbitBlock: List[bool] = Field(default_factory=list)  # type 1, R
    bitBlock: List[bool] = Field(default_factory=list)  # type 2, R/W
    rbyteBlock: List[int] = Field(default_factory=list)  # type 3, R
    byteBlock: List[int] = Field(default_factory=list)  # type 4, R/W
    rwordBlock: List[int] = Field(default_factory=list)  # type 5, R
    wordBlock: List[int] = Field(default_factory=list)  # type 6, R/W
    rdwordBlock: List[int] = Field(default_factory=list)  # type 7, R
    dwordBlock: List[int] = Field(default_factory=list)  # type 8, R/W
    rqwordBlock: List[int] = Field(default_factory=list)  # type 9, R
    qwordBlock: List[int] = Field(default_factory=list)  # type 10, R/W


# ─── NcMemory ────────────────────────────────────────────────────────────────


class NcMemory(BaseModel):
    """NC file system memory info. All R."""

    totalCapacity: float = 0.0  # R (bytes)
    usedCapacity: float = 0.0  # R (bytes)
    freeCapacity: float = 0.0  # R (bytes)
    rootPath: str = ""  # R


# ─── ToolArea ────────────────────────────────────────────────────────────────


class ToolInfo(BaseModel):
    """Full tool info for magazine/registered tools."""

    locationNumber: int = 0
    toolName: str = ""
    toolNumber: int = 0
    numberOfEdges: int = 1
    toolEnabled: int = 1
    magazineNumber: int = 1
    sisterToolNumber: int = 0
    toolLifeUnit: int = 0
    toolGroupNumber: int = 0
    toolUseOrderNumber: int = 0
    toolStatus: int = 0
    toolEdge: List[ToolEdge] = Field(default_factory=list)


class Magazine(BaseModel):
    """Tool magazine."""

    magazineNumber: int = 1
    tools: List[ToolInfo] = Field(default_factory=list)


class ToolArea(BaseModel):
    """Tool area: magazines and registered tools."""

    numberOfToolOffsets: int = 0  # R
    magazine: List[Magazine] = Field(default_factory=list)


# ─── Buffer (Sensor Stream) ─────────────────────────────────────────────────


class StreamConfig(BaseModel):
    """Single stream within buffer."""

    streamEnabled: bool = False  # R/W
    streamFrequency: int = 1000  # R/W (Hz)
    streamCategory: int = 0  # R/W
    streamSubcategory: int = 0  # R/W
    streamType: int = 0  # R/W (KCNC only)
    streamStartBit: int = 0  # R/W (KCNC only, bit type)
    streamEndBit: int = 0  # R/W (KCNC only, bit type)
    value: float = 0.0  # R (last collected)


class Buffer(BaseModel):
    """Sensor data collection buffer."""

    bufferEnabled: bool = False  # R
    numberOfStream: int = 0  # R
    statusOfStream: int = 0  # R/W
    modOfStream: int = 0  # R
    machineChannelOfStream: int = 0  # R
    periodOfStream: int = 100  # R/W (ms, max 10000)
    triggerOfStream: int = 0  # R/W
    frequencyOfStream: int = 1000  # R/W (Hz, default 1000)
    stream: List[StreamConfig] = Field(default_factory=list)


# ─── MachineData (Top-level) ────────────────────────────────────────────────


class MachineData(BaseModel):
    """Top-level machine data model.

    Represents a single CNC machine's complete state.
    """

    # Machine identity
    machineId: int = 1
    machineName: str = ""
    vendorId: int = 1  # 1=FANUC, 2=SIEMENS, 3=CSCAM, 4=MITSUBISHI, 5=KCNC
    vendorName: str = ""
    modelName: str = ""

    # Sub-structures
    channel: List[Channel] = Field(default_factory=list)
    plc: PlcData = Field(default_factory=PlcData)
    ncMemory: NcMemory = Field(default_factory=NcMemory)
    toolArea: ToolArea = Field(default_factory=ToolArea)
    buffer: Buffer = Field(default_factory=Buffer)


# ─── API Request/Response Schemas ────────────────────────────────────────────


class DataRequest(BaseModel):
    """Request for getData / updateData."""

    address: str  # e.g. "data://machine/channel/axis/machinePosition"
    filter: str = ""  # e.g. "machine=1&channel=1&axis=1"


class DataUpdateRequest(BaseModel):
    """Request for updateData."""

    address: str
    filter: str = ""
    value: Any = None


class BatchDataRequest(BaseModel):
    """Batch getData request."""

    items: List[DataRequest]


class DataResponse(BaseModel):
    """Response for getData."""

    address: str
    filter: str = ""
    value: Any = None
    success: bool = True
    error: Optional[str] = None


class BatchDataResponse(BaseModel):
    """Batch getData response."""

    items: List[DataResponse]


class PlcReadRequest(BaseModel):
    """Request for getPlcSignal."""

    machine: int = 1
    type: int  # 1-10
    startAddress: int = 0
    count: int = 1


class PlcWriteRequest(BaseModel):
    """Request for setPlcSignal."""

    machine: int = 1
    type: int  # 2,4,6,8,10 only (R/W types)
    startAddress: int = 0
    data: List[Any] = Field(default_factory=list)


class PlcResponse(BaseModel):
    """Response for PLC operations."""

    machine: int
    type: int
    startAddress: int
    count: int
    data: List[Any] = Field(default_factory=list)
    success: bool = True
    error: Optional[str] = None


class SubscribeRequest(BaseModel):
    """Request for subscribeData."""

    address: str
    filter: str = ""
    interval: int = 1000  # ms


class SubscribeResponse(BaseModel):
    """Response for subscribeData."""

    subscriptionId: str
    address: str
    filter: str = ""
    interval: int = 1000


class MachineListResponse(BaseModel):
    """Machine list response."""

    machines: List[Dict[str, Any]]


class SimulationStatus(BaseModel):
    """Simulation engine status."""

    running: bool = False
    tick_count: int = 0
    interval_ms: int = 500
    machines: List[int] = Field(default_factory=list)


class TriggerAlarmRequest(BaseModel):
    """Manual alarm trigger."""

    machine: int = 1
    channel: int = 1
    alarmNumber: str = "1000"
    alarmText: str = "Test alarm"
    alarmCategory: str = "WARNING"


class ToolChangeRequest(BaseModel):
    """Manual tool change."""

    machine: int = 1
    channel: int = 1
    toolNumber: int = 1
    edgeNumber: int = 1


# ─── R/W Field Registry ─────────────────────────────────────────────────────

# Fields that can be written via updateData API
WRITABLE_FIELDS = {
    # Axis
    "axisLimitPlus",
    "axisLimitMinus",
    "workAreaLimitPlus",
    "workAreaLimitMinus",
    "workAreaLimitPlusEnabled",
    "workAreaLimitMinusEnabled",
    "machineOrigin",
    # WorkCounter
    "currentWorkCounter",
    "targetWorkCounter",
    # Variable
    "userVariable",
    # WorkOffset
    "workOffsetValue",
    "workOffsetRotation",
    "workOffsetScalingFactor",
    "workOffsetMirroringEnabled",
    "workOffsetFine",
    # ControlOption
    "singleBlock",
    "dryRun",
    "optionalStop",
    "blockSkip",
    "machineLock",
    # Buffer
    "statusOfStream",
    "periodOfStream",
    "triggerOfStream",
    "frequencyOfStream",
    "streamEnabled",
    "streamFrequency",
    "streamCategory",
    "streamSubcategory",
    "streamType",
    "streamStartBit",
    "streamEndBit",
}

# PLC types that are writable (even-numbered types)
PLC_WRITABLE_TYPES = {2, 4, 6, 8, 10}

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Union

__NAMESPACE__ = "http://digital-thread.re/dt_asset"


@dataclass
class AccelerationMeasure:
    class Meta:
        name = "acceleration_measure"

    acceleration_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class AdaptiveControl:
    class Meta:
        name = "adaptive_control"


@dataclass
class Address:
    class Meta:
        name = "address"

    internal_location: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    street_number: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    street: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    postal_box: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    town: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    region: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    postal_code: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    country: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    facsimile_number: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    telephone_number: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    electronic_mail_address: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    telex_number: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


class AheadOrBehind(Enum):
    AHEAD = "ahead"
    EXACT = "exact"
    BEHIND = "behind"


@dataclass
class AngleOrLength:
    class Meta:
        name = "angle_or_length"

    plane_angle_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    length_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class AngleTaper:
    class Meta:
        name = "angle_taper"

    angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ApplicationContext:
    class Meta:
        name = "application_context"

    application: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ApprovalStatus:
    class Meta:
        name = "approval_status"

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class AxisCapability:
    class Meta:
        name = "axis_capability"

    number_of_axes: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    number_of_simultanious_axes: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


class BSplineCurveForm(Enum):
    POLYLINE_FORM = "polyline_form"
    CIRCULAR_ARC = "circular_arc"
    ELLIPTIC_ARC = "elliptic_arc"
    PARABOLIC_ARC = "parabolic_arc"
    HYPERBOLIC_ARC = "hyperbolic_arc"
    UNSPECIFIED = "unspecified"


@dataclass
class BooleanExpression:
    class Meta:
        name = "boolean_expression"


class BottomOrSide(Enum):
    BOTTOM = "bottom"
    SIDE = "side"
    BOTTOM_AND_SIDE = "bottom_and_side"


@dataclass
class BoundedPcurve:
    class Meta:
        name = "bounded_pcurve"


@dataclass
class ChamferedCorner:
    class Meta:
        name = "chamfered_corner"

    corner_chamfer_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    corner_chamfer_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    corner_chamfer_width: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Channel:
    class Meta:
        name = "channel"

    its_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class CharacterizedObject:
    class Meta:
        name = "characterized_object"

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class CircularOffset:
    class Meta:
        name = "circular_offset"

    angular_offset: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    index: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class CircularOmit:
    class Meta:
        name = "circular_omit"

    index: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Coating:
    class Meta:
        name = "coating"

    coating_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    coating_process: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ConstCuttingSpeed:
    class Meta:
        name = "const_cutting_speed"

    speed: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    max_speed: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ConstSpindleSpeed:
    class Meta:
        name = "const_spindle_speed"

    rot_speed: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


class ContactType(Enum):
    SIDE = "side"
    FRONT = "front"


class CoolantSelect(Enum):
    FLOOD = "flood"
    MIST = "mist"
    THROUGH_TOOL = "through_tool"


class CoolantType(Enum):
    AIR = "AIR"
    FLOOD = "FLOOD"
    MICRO = "MICRO"
    MIST = "MIST"
    NONE = "NONE"


@dataclass
class CountMeasure:
    class Meta:
        name = "count_measure"

    count_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


class CutmodeType(Enum):
    CLIMB = "climb"
    CONVENTIONAL = "conventional"


@dataclass
class CuttingCondition:
    class Meta:
        name = "cutting_condition"

    condition_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Date:
    class Meta:
        name = "date"

    year_component: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class DateTime:
    class Meta:
        name = "date_time"

    date: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    time: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class DayInMonthNumber:
    class Meta:
        name = "day_in_month_number"

    day_in_month_number: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class DefaultLanguageString:
    class Meta:
        name = "default_language_string"

    default_language_string: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class DocumentCreationProperty:
    class Meta:
        name = "document_creation_property"

    creating_interface: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    creating_system: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    operating_system: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class DocumentLocationProperty:
    class Meta:
        name = "document_location_property"

    location_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class DrillingTypeStrategy:
    class Meta:
        name = "drilling_type_strategy"

    reduced_cut_at_start: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    reduced_feed_at_start: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    depth_of_start: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    reduced_cut_at_end: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    reduced_feed_at_end: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    depth_of_end: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


class DtAssetKind(Enum):
    INSTANCE = "instance"
    TYPE = "type"


@dataclass
class DtElement:
    class Meta:
        name = "dt_element"

    element_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    category: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    display_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    element_description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


class DtKeyType(Enum):
    DT_GLOBAL_ASSET = "DT_GLOBAL_ASSET"
    DT_ASSET = "DT_ASSET"
    DT_PROJECT = "DT_PROJECT"
    DT_ELEMENT = "DT_ELEMENT"
    DT_ELEMENT_LIST = "DT_ELEMENT_LIST"
    DT_PROPERTY = "DT_PROPERTY"
    DT_MATERIAL = "DT_MATERIAL"
    DT_CUTTING_TOOL = "DT_CUTTING_TOOL"
    DT_CUTTING_TOOL_MDES = "DT_CUTTING_TOOL_MDES"
    DT_CUTTING_TOOL_13399 = "DT_CUTTING_TOOL_13399"
    DT_MACHINE_TOOL = "DT_MACHINE_TOOL"
    DT_NCCODE = "DT_NCCODE"
    DT_FILE = "DT_FILE"
    DT_BLOB = "DT_BLOB"
    DT_IMAGE = "DT_IMAGE"
    ETC = "ETC"


@dataclass
class Duration:
    class Meta:
        name = "duration"

    time: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    time_unit: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class DwellRevolution:
    class Meta:
        name = "dwell_revolution"

    dwell_revolution: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class DwellSelect:
    class Meta:
        name = "dwell_select"

    dwell_time: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    dwell_revolution: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class DwellTime:
    class Meta:
        name = "dwell_time"

    time_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ElectricCurrentMeasure:
    class Meta:
        name = "electric_current_measure"

    electric_current_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Electrical:
    class Meta:
        name = "electrical"

    electric_phase: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    electric_power: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    electrical_current: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    electrical_frequency: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    electrical_grounding: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    electrical_voltage: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ElementCapability:
    class Meta:
        name = "element_capability"

    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class EmissionProperty:
    class Meta:
        name = "emission_property"

    emission_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    weight: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Executable:
    class Meta:
        name = "executable"

    its_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class FeedPerRevType:
    class Meta:
        name = "feed_per_rev_type"

    feed_per_rev_type: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class FeedSelect:
    class Meta:
        name = "feed_select"

    feed_velocity_type: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    feed_per_rev_type: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class FeedVelocityType:
    class Meta:
        name = "feed_velocity_type"

    speed_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


class FittingType(Enum):
    SHAFT = "shaft"
    HOLE = "hole"


class FixtureStyle(Enum):
    CHUCK_FIXTURE = "CHUCK_FIXTURE"
    HOLE = "HOLE"
    T_SLOT_FIXTURE = "T_SLOT_FIXTURE"
    VACUUM = "VACUUM"


class HandOfCutType(Enum):
    LEFT = "left"
    NEUTRAL = "neutral"
    RIGHT = "right"


class HandOfToolType(Enum):
    LEFT = "left"
    RIGHT = "right"
    NEUTRAL = "neutral"


@dataclass
class HoleBottomCondition:
    class Meta:
        name = "hole_bottom_condition"


@dataclass
class HourInDay:
    class Meta:
        name = "hour_in_day"

    hour_in_day: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Hydraulics:
    class Meta:
        name = "hydraulics"

    type_of_hydraulic_oil: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    pump_outlet_pressure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    capacity_of_hydraulics_tank: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Identifier:
    class Meta:
        name = "identifier"

    identifier: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


class Interpolation(Enum):
    CIRCULAR = "CIRCULAR"
    HELICAL = "HELICAL"
    LINEAR = "LINEAR"
    NURBS = "NURBS"
    OTHER = "OTHER"


@dataclass
class JerkMeasure:
    class Meta:
        name = "jerk_measure"

    jerk_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class KinematicLink:
    class Meta:
        name = "kinematic_link"


@dataclass
class Label:
    class Meta:
        name = "label"

    label: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Language:
    class Meta:
        name = "language"

    country_code: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    language_code: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


class LeftOrRight(Enum):
    LEFT = "left"
    RIGHT = "right"


@dataclass
class LengthMeasure:
    class Meta:
        name = "length_measure"

    length_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Location:
    class Meta:
        name = "location"

    location_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    location_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    location_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Locator:
    class Meta:
        name = "locator"

    business_unit: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    plant_location: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    building: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    cell: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


class MachineClass(Enum):
    DRILLING_MACHINE = "DRILLING_MACHINE"
    GUNDRILL_MACHINE = "GUNDRILL_MACHINE"
    MACHINING_CENTRE = "MACHINING_CENTRE"
    MILLING_MACHINE = "MILLING_MACHINE"
    MULTI_TASKING_MACHINE = "MULTI_TASKING_MACHINE"
    TURNING_MACHINE = "TURNING_MACHINE"


@dataclass
class MachineFunctions:
    class Meta:
        name = "machine_functions"


@dataclass
class MachineSize:
    class Meta:
        name = "machine_size"

    machine_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    machine_width: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    machine_height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class MachineTool:
    class Meta:
        name = "machine_tool"

    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


class MachiningCapabilityProfile(Enum):
    BORING_CAPABILITY = "BORING_CAPABILITY"
    DRILLING_CAPABILITY = "DRILLING_CAPABILITY"
    GUNDRILL_CAPABILITY = "GUNDRILL_CAPABILITY"
    MILLING_CAPABILITY = "MILLING_CAPABILITY"
    TURNING_CAPABILITY = "TURNING_CAPABILITY"


@dataclass
class MachiningSize:
    class Meta:
        name = "machining_size"

    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    x: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    y: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    z: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class MachiningTool:
    class Meta:
        name = "machining_tool"

    its_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class MassMeasure:
    class Meta:
        name = "mass_measure"

    mass_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class MaterialDesignation:
    class Meta:
        name = "material_designation"

    material_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


class MeansOfCoolantDelivery(Enum):
    EXTERNAL = "EXTERNAL"
    THRU_SPINDLE = "THRU_SPINDLE"
    THRU_TURRET = "THRU_TURRET"


@dataclass
class MeasuringCapability:
    class Meta:
        name = "measuring_capability"

    measuring_accuracy: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class MinuteInHour:
    class Meta:
        name = "minute_in_hour"

    minute_in_hour: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class MonthInYearNumber:
    class Meta:
        name = "month_in_year_number"

    month_in_year_number: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class NcConstant:
    class Meta:
        name = "nc_constant"

    its_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_value: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class NcVariable:
    class Meta:
        name = "nc_variable"

    its_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    initial_value: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class NonNegativeLengthMeasure:
    class Meta:
        name = "non_negative_length_measure"

    length_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Organization:
    class Meta:
        name = "organization"

    delivery_address: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    organization_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    organization_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    postal_address: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    visitor_address: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


class PalletStorageConfiguration(Enum):
    CAROUSEL = "CAROUSEL"
    CAROUSEL_2_PLACE = "CAROUSEL_2_PLACE"
    CHAIN = "CHAIN"
    FIXED_2_PLACE = "FIXED_2_PLACE"
    MULTI_STOREY = "MULTI_STOREY"
    STRAIGHT_LINE = "STRAIGHT_LINE"


@dataclass
class ParameterValue:
    class Meta:
        name = "parameter_value"

    parameter_value: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


class PathmodeType(Enum):
    FORWARD = "forward"
    ZIGZAG = "zigzag"


@dataclass
class Person:
    class Meta:
        name = "person"

    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    last_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    first_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    middle_names: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    prefix_titles: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    suffix_titles: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class PlaneAngleMeasure:
    class Meta:
        name = "plane_angle_measure"

    plane_angle_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PlibClassReference:
    class Meta:
        name = "plib_class_reference"

    code: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    supplier_bsu: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    version: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PlusMinusBounds:
    class Meta:
        name = "plus_minus_bounds"

    lower_bound: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    significant_digits: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    upper_bound: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    value_determination: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class PlusMinusValue:
    class Meta:
        name = "plus_minus_value"

    upper_limit: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    lower_limit: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    significant_digits: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PocketBottomCondition:
    class Meta:
        name = "pocket_bottom_condition"


@dataclass
class PositiveLengthMeasure:
    class Meta:
        name = "positive_length_measure"

    non_negative_length_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PositiveRatioMeasure:
    class Meta:
        name = "positive_ratio_measure"

    ratio_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PowerMeasure:
    class Meta:
        name = "power_measure"

    power_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PressureMeasure:
    class Meta:
        name = "pressure_measure"

    pressure_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


class ProbeType(Enum):
    NULLING = "NULLING"
    PROPORTIONAL = "PROPORTIONAL"
    SWITCHING = "SWITCHING"


@dataclass
class ProcessModel:
    class Meta:
        name = "process_model"

    ini_data_file: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PropertyParameter:
    class Meta:
        name = "property_parameter"

    parameter_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PropertyValue:
    class Meta:
        name = "property_value"

    value_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class RapidMovement:
    class Meta:
        name = "rapid_movement"


@dataclass
class RatioMeasure:
    class Meta:
        name = "ratio_measure"

    ratio_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class RectangularOmit:
    class Meta:
        name = "rectangular_omit"

    row_index: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    column_index: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class RepresentationContext:
    class Meta:
        name = "representation_context"

    context_identifier: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    context_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class RepresentationItem:
    class Meta:
        name = "representation_item"

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class RotAccelerationMeasure:
    class Meta:
        name = "rot_acceleration_measure"

    rot_acceleration_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


class RotDirection(Enum):
    CW = "cw"
    CCW = "ccw"


@dataclass
class RotJerkMeasure:
    class Meta:
        name = "rot_jerk_measure"

    rot_jerk_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class RotSpeedMeasure:
    class Meta:
        name = "rot_speed_measure"

    rot_speed_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class RoundedCorner:
    class Meta:
        name = "rounded_corner"

    corner_radius: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class SecondInMinute:
    class Meta:
        name = "second_in_minute"

    second_in_minute: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


class SensorDimensionality(Enum):
    ONE_D = "ONE_D"
    TWO_D = "TWO_D"
    THREE_D = "THREE_D"


@dataclass
class SetupInstruction:
    class Meta:
        name = "setup_instruction"

    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    external_document: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ShapeDefinition:
    class Meta:
        name = "shape_definition"

    product_definition_shape: Optional["ProductDefinitionShape"] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    shape_aspect: Optional["ShapeAspect"] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    shape_aspect_relationship: Optional["ShapeAspectRelationship"] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ShapeTolerance:
    class Meta:
        name = "shape_tolerance"

    length_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class SlotEndType:
    class Meta:
        name = "slot_end_type"


@dataclass
class SpecificationUsageConstraint:
    class Meta:
        name = "specification_usage_constraint"

    element: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    class_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class SpeedMeasure:
    class Meta:
        name = "speed_measure"

    speed_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


class SpeedName(Enum):
    RAPID = "RAPID"


@dataclass
class SpindleCapability:
    class Meta:
        name = "spindle_capability"

    spindle_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    spindle_power: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_drive_speed: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class SpindleRange:
    class Meta:
        name = "spindle_range"

    minimum_drive_speed: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_drive_speed: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    minimum_drive_torque: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_drive_torque: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class State:
    class Meta:
        name = "state"

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


class StrokeConnectionStrategy(Enum):
    STRAGHTLINE = "straghtline"
    LIFT_SHIFT_PLUNGE = "lift_shift_plunge"
    DEGOUGE = "degouge"
    LOOP_BACK = "loop_back"


@dataclass
class Substrate:
    class Meta:
        name = "substrate"

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class TSlot:
    class Meta:
        name = "t_slot"

    number_of_t_slots: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    t_slots_size: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    distance_between_t_slot_centers: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Text:
    class Meta:
        name = "text"

    text: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


class ThreadCutDepthType(Enum):
    CONSTANT_DEPTH = "constant_depth"
    VARIABLE_DEPTH = "variable_depth"
    CONSTANT_REMOVAL_AMOUNT = "constant_removal_amount"


class ThreadHandType(Enum):
    LEFT = "left"
    RIGHT = "right"


class ThreadProfileType(Enum):
    FULL_PROFILE = "full_profile"
    PARTIAL_PROFILE = "partial_profile"


class ThreadType(Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"


class ThreadingDirectionType(Enum):
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    LEFT_ZIGZAG = "left_zigzag"
    RIGHT_ZIGZAG = "right_zigzag"


@dataclass
class ThroughProfileFloor:
    class Meta:
        name = "through_profile_floor"


@dataclass
class TimeMeasure:
    class Meta:
        name = "time_measure"

    time_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Tolerances:
    class Meta:
        name = "tolerances"

    chordal_tolerance: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    scallop_height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ToolAssembly:
    class Meta:
        name = "tool_assembly"

    tool_number: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    tool_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    tool_size: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


class ToolCompensation(Enum):
    TOOL_LENGTH = "TOOL_LENGTH"
    TOOL_RADIUS = "TOOL_RADIUS"


@dataclass
class ToolDirection:
    class Meta:
        name = "tool_direction"


class ToolReferencePoint(Enum):
    TCP = "tcp"
    CCP = "ccp"


class ToolStorageConfiguration(Enum):
    BI_DIRECTIONAL = "BI_DIRECTIONAL"
    BOX_MATRIX = "BOX_MATRIX"
    UNI_DIRECTIONAL = "UNI_DIRECTIONAL"


class ToolpathType(Enum):
    APPROACH = "approach"
    LIFT = "lift"
    CONNECT = "connect"
    NON_CONTACT = "non_contact"
    CONTACT = "contact"
    TRAJECTORY_PATH = "trajectory_path"


@dataclass
class TopologicalRegion:
    class Meta:
        name = "topological_region"


@dataclass
class TorqueMeasure:
    class Meta:
        name = "torque_measure"

    torque_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class TouchProbe:
    class Meta:
        name = "touch_probe"

    its_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class TouchProbing:
    class Meta:
        name = "touch_probing"


@dataclass
class Transformation:
    class Meta:
        name = "transformation"


@dataclass
class TurningMachiningStrategy:
    class Meta:
        name = "turning_machining_strategy"

    overcut_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    allow_multiple_passes: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    cutting_depth: list[float] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    variable_feedrate: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Two5DMillingStrategy:
    class Meta:
        name = "two5D_milling_strategy"

    overlap: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    allow_multiple_passes: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_milling_tolerances: Optional[Tolerances] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Unit:
    class Meta:
        name = "unit"

    unit_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


class UnitsType(Enum):
    INCH = "INCH"
    INCH_AND_METRIC = "INCH_AND_METRIC"
    METRIC = "METRIC"


@dataclass
class VelocityMeasure:
    class Meta:
        name = "velocity_measure"

    velocity_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class VolumeMeasure:
    class Meta:
        name = "volume_measure"

    volume_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class YearNumber:
    class Meta:
        name = "year_number"

    year_number: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ApplicationContextElement:
    class Meta:
        name = "application_context_element"

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    frame_of_reference: Optional[ApplicationContext] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Approval:
    class Meta:
        name = "approval"

    status: Optional[ApprovalStatus] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    level: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class BarFeeder(ElementCapability):
    class Meta:
        name = "bar_feeder"

    minimum_stock_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_stock_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_stock_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class BinaryBooleanExpression(BooleanExpression):
    class Meta:
        name = "binary_boolean_expression"

    operand1: Optional[BooleanExpression] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    operand2: Optional[BooleanExpression] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class BlindBottomCondition(HoleBottomCondition):
    class Meta:
        name = "blind_bottom_condition"


@dataclass
class CalendarDate(Date):
    class Meta:
        name = "calendar_date"

    day_component: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    month_component: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class CartesianCoordinateSpace:
    class Meta:
        name = "cartesian_coordinate_space"

    unit_of_values: list[Unit] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class CenterMilling(Two5DMillingStrategy):
    class Meta:
        name = "center_milling"


@dataclass
class Chuck(ElementCapability):
    class Meta:
        name = "chuck"

    minimum_part_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_part_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    number_of_jaws: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Collet(ElementCapability):
    class Meta:
        name = "collet"

    collet_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    minimum_part_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_part_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ContourParallel(Two5DMillingStrategy):
    class Meta:
        name = "contour_parallel"

    rotation_direction: Optional[RotDirection] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    cutmode: Optional[CutmodeType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ContourSpiral(Two5DMillingStrategy):
    class Meta:
        name = "contour_spiral"

    rotation_direction: Optional[RotDirection] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    cutmode: Optional[CutmodeType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Coolant(ElementCapability):
    class Meta:
        name = "coolant"

    coolant_type: Optional[CoolantType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    means_of_delivery: Optional[MeansOfCoolantDelivery] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    capacity_of_coolant_tank: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    coolant_weight: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class CoordinatedUniversalTimeOffset:
    class Meta:
        name = "coordinated_universal_time_offset"

    hour_offset: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    minute_offset: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    sense: Optional[AheadOrBehind] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class DescriptiveParameter(PropertyParameter):
    class Meta:
        name = "descriptive_parameter"

    descriptive_string: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class DtCuttingTool(DtElement):
    class Meta:
        name = "dt_cutting_tool"


@dataclass
class DtFile(DtElement):
    class Meta:
        name = "dt_file"

    content_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    value: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    keys: list["DtKeyValue"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class DtKeyValue:
    class Meta:
        name = "dt_key_value"

    key: Optional[DtKeyType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    value: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class DtMachineTool(DtElement):
    class Meta:
        name = "dt_machine_tool"

    machine_tool: Optional[MachineTool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class DtMaterial(DtElement):
    class Meta:
        name = "dt_material"

    standard_identifier: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    material_identifier: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    material_property: list[PropertyParameter] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class DtProperty(DtElement):
    class Meta:
        name = "dt_property"

    type_value: Optional[str] = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    value: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    value_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ExplicitStrategy(Two5DMillingStrategy):
    class Meta:
        name = "explicit_strategy"


@dataclass
class ExplicitTurningStrategy(TurningMachiningStrategy):
    class Meta:
        name = "explicit_turning_strategy"


@dataclass
class ExternalFileIdAndLocation:
    class Meta:
        name = "external_file_id_and_location"

    external_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    location: Optional[DocumentLocationProperty] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class FreeformStrategy:
    class Meta:
        name = "freeform_strategy"

    pathmode: Optional[PathmodeType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    cutmode: Optional[CutmodeType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_milling_tolerances: Optional[Tolerances] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    stepover: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class GeometricRepresentationItem(RepresentationItem):
    class Meta:
        name = "geometric_representation_item"


@dataclass
class Grade:
    class Meta:
        name = "grade"

    coating: Optional[Coating] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    cutting_condition: list[CuttingCondition] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    identifier: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    standard_designation: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    substrate: Optional[Substrate] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    workpiece_material: list[MaterialDesignation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Installation:
    class Meta:
        name = "installation"

    weight: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    size: Optional[MachineSize] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    electrical: Optional[Electrical] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    air_pressure_requirement: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    water_flow_rate: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    hydraulics: Optional[Hydraulics] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class KinematicJoint:
    class Meta:
        name = "kinematic_joint"

    first_link: Optional[KinematicLink] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    second_link: Optional[KinematicLink] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class LimitsAndFits:
    class Meta:
        name = "limits_and_fits"

    deviation: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    grade: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_fitting_type: Optional[FittingType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class LoopSlotEndType(SlotEndType):
    class Meta:
        name = "loop_slot_end_type"


@dataclass
class MachineToolAxis(ElementCapability):
    class Meta:
        name = "machine_tool_axis"

    axis_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class MachineToolElement:
    class Meta:
        name = "machine_tool_element"

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    weight: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    capabilities: list[ElementCapability] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class MachiningCapability:
    class Meta:
        name = "machining_capability"

    capability: Optional[MachiningCapabilityProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    machining_accuracy: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    machining_size: Optional[MachiningSize] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Material:
    class Meta:
        name = "material"

    standard_identifier: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    material_identifier: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    material_property: list[PropertyParameter] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class MultipleArityBooleanExpression(BooleanExpression):
    class Meta:
        name = "multiple_arity_boolean_expression"

    operands: list[BooleanExpression] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class NcController:
    class Meta:
        name = "nc_controller"

    controller_model: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    controller_manufacturer: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    units: Optional[UnitsType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_number_of_simultaneous_control_axes: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_total_number_of_control_feed_axes: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_total_number_of_control_spindles: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    minimum_linear_increment: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    minimum_angle_increment: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_number_of_multi_channel_control: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    cycle_functions: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    interpolation_functions: list[Interpolation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    look_ahead: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    adaptive_control: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    miscellaneous_controller_functions: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    program_memory_size: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    cutting_feed_rate_override: list[float] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    rapid_traverse_override: list[float] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    tool_compensation_functions: list[ToolCompensation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    time_sampling: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    clock_frequency: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class NcFunction(Executable):
    class Meta:
        name = "nc_function"


@dataclass
class NumericParameter(PropertyParameter):
    class Meta:
        name = "numeric_parameter"

    its_parameter_value: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_parameter_unit: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class OffsetVector:
    class Meta:
        name = "offset_vector"

    translate: list[NcVariable] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "max_occurs": 3,
        },
    )
    rotate: list[NcVariable] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "max_occurs": 3,
        },
    )


@dataclass
class OpenSlotEndType(SlotEndType):
    class Meta:
        name = "open_slot_end_type"


@dataclass
class PersonAndAddress:
    class Meta:
        name = "person_and_address"

    its_person: Optional[Person] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_address: Optional[Address] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class PersonInOrganization:
    class Meta:
        name = "person_in_organization"

    associated_organization: Optional[Organization] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    associated_person: Optional[Person] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    location: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    role: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PlanarPocketBottomCondition(PocketBottomCondition):
    class Meta:
        name = "planar_pocket_bottom_condition"


@dataclass
class PlibPropertyReference:
    class Meta:
        name = "plib_property_reference"

    code: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    name_scope: Optional[PlibClassReference] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    version: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ProcessModelList:
    class Meta:
        name = "process_model_list"

    its_list: list[ProcessModel] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ProgramStructure(Executable):
    class Meta:
        name = "program_structure"


@dataclass
class RadiusedSlotEndType(SlotEndType):
    class Meta:
        name = "radiused_slot_end_type"


@dataclass
class RangeOfMotion:
    class Meta:
        name = "range_of_motion"

    axis_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    motion_range: Optional[AngleOrLength] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Representation:
    class Meta:
        name = "representation"

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    items: list[RepresentationItem] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    context_of_items: Optional[RepresentationContext] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ReturnHome(RapidMovement):
    class Meta:
        name = "return_home"


@dataclass
class Rvalue:
    class Meta:
        name = "rvalue"

    nc_constant: Optional[NcConstant] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    nc_variable: Optional[NcVariable] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Specification:
    class Meta:
        name = "specification"

    constraint: list[SpecificationUsageConstraint] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    specification_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    specification_description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    specification_class: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class SpeedSelect:
    class Meta:
        name = "speed_select"

    const_spindle_speed: Optional[ConstSpindleSpeed] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    const_cutting_speed: Optional[ConstCuttingSpeed] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Spindle(ElementCapability):
    class Meta:
        name = "spindle"

    spindle_power: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    spindle_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    spindle_manufacturer: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    manufacturer_model_designation: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    range: list[SpindleRange] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class StandardMachiningProcess:
    class Meta:
        name = "standard_machining_process"

    process_description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    type_of_machining: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    power: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    electric_power: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    process_emission: list[EmissionProperty] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class StringWithLanguage:
    class Meta:
        name = "string_with_language"

    contents: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    language_specification: Optional[Language] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Tailstock(ElementCapability):
    class Meta:
        name = "tailstock"

    spindle_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    taper: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_workpiece_weight_of_quill: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Technology:
    class Meta:
        name = "technology"

    feedrate: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    feedrate_reference: Optional[ToolReferencePoint] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ThreadStrategy(TurningMachiningStrategy):
    class Meta:
        name = "thread_strategy"

    cut_in_amount_function: Optional[ThreadCutDepthType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    threading_direction: Optional[ThreadingDirectionType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    path_return_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    lift_height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ThreeAxes(ToolDirection):
    class Meta:
        name = "three_axes"


@dataclass
class ThroughBottomCondition(HoleBottomCondition):
    class Meta:
        name = "through_bottom_condition"


@dataclass
class ThroughPocketBottomCondition(PocketBottomCondition):
    class Meta:
        name = "through_pocket_bottom_condition"


@dataclass
class ToolDirectionForMilling(ToolDirection):
    class Meta:
        name = "tool_direction_for_milling"


@dataclass
class ToolHandlingUnit(ElementCapability):
    class Meta:
        name = "tool_handling_unit"


@dataclass
class TopologicalRepresentationItem(RepresentationItem):
    class Meta:
        name = "topological_representation_item"


@dataclass
class Transformation2D(Transformation):
    class Meta:
        name = "transformation_2d"


@dataclass
class Transformation3D(Transformation):
    class Meta:
        name = "transformation_3d"


@dataclass
class TwoAxes(ToolDirection):
    class Meta:
        name = "two_axes"


@dataclass
class UnaryBooleanExpression(BooleanExpression):
    class Meta:
        name = "unary_boolean_expression"

    operand: Optional[BooleanExpression] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ValueList(PropertyValue):
    class Meta:
        name = "value_list"

    values: list[PropertyValue] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ValueWithUnit(PropertyValue):
    class Meta:
        name = "value_with_unit"

    significant_digits: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    unit_component: Optional[Unit] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class AndExpression(MultipleArityBooleanExpression):
    class Meta:
        name = "and_expression"


@dataclass
class Assignment(ProgramStructure):
    class Meta:
        name = "assignment"

    its_lvalue: Optional[NcVariable] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_rvalue: Optional[Rvalue] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class CartesianCoordinateSpace2D(CartesianCoordinateSpace):
    class Meta:
        name = "cartesian_coordinate_space_2d"


@dataclass
class CartesianCoordinateSpace3D(CartesianCoordinateSpace):
    class Meta:
        name = "cartesian_coordinate_space_3d"


@dataclass
class ComparisonExpression(BooleanExpression):
    class Meta:
        name = "comparison_expression"

    operand1: Optional[NcVariable] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    operand2: Optional[Rvalue] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Curve(GeometricRepresentationItem):
    class Meta:
        name = "curve"


@dataclass
class CuttingComponent:
    class Meta:
        name = "cutting_component"

    tool_functional_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_material: Optional[Material] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    expected_tool_life: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_technology: Optional[Technology] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class CuttingDataAssociation:
    class Meta:
        name = "cutting_data_association"

    associated_material: Optional[MaterialDesignation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    depth_of_cut: Optional[ValueWithUnit] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    feed: Optional[ValueWithUnit] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    speed: Optional[ValueWithUnit] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class DefinitionalRepresentation(Representation):
    class Meta:
        name = "definitional_representation"


@dataclass
class DeviceId:
    class Meta:
        name = "device_id"

    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    model_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    serial_number: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    manufacturer: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    date_manufactured: Optional[CalendarDate] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Direction(GeometricRepresentationItem):
    class Meta:
        name = "direction"

    direction_ratios: list[float] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "max_occurs": 3,
        },
    )


@dataclass
class DisplayMessage(NcFunction):
    class Meta:
        name = "display_message"

    its_text: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class DocumentSizeProperty:
    class Meta:
        name = "document_size_property"

    file_size: Optional[ValueWithUnit] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    page_count: Optional[ValueWithUnit] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class DtReference(DtElement):
    class Meta:
        name = "dt_reference"

    keys: list[DtKeyValue] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ElementLinkAssociation:
    class Meta:
        name = "element_link_association"

    element: Optional[MachineToolElement] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    machine_link: Optional[KinematicLink] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class EnvironmentalEvaluation:
    class Meta:
        name = "environmental_evaluation"

    evaluation_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    power_in_idling: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    time_for_warming_up: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    power_for_standard_machining: list[StandardMachiningProcess] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ExchangePallet(NcFunction):
    class Meta:
        name = "exchange_pallet"


@dataclass
class FiveAxesConstTiltYaw(ToolDirectionForMilling):
    class Meta:
        name = "five_axes_const_tilt_yaw"

    tilt_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    yaw_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class FiveAxesVarTiltYaw(ToolDirectionForMilling):
    class Meta:
        name = "five_axes_var_tilt_yaw"


@dataclass
class FlatHoleBottom(BlindBottomCondition):
    class Meta:
        name = "flat_hole_bottom"


@dataclass
class GradeRelationship:
    class Meta:
        name = "grade_relationship"

    related: Optional[Grade] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relating: Optional[Grade] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relation_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class IfStatement(ProgramStructure):
    class Meta:
        name = "if_statement"

    condition: Optional[BooleanExpression] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    true_branch: Optional[Executable] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    false_branch: Optional[Executable] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class IndexPallet(NcFunction):
    class Meta:
        name = "index_pallet"

    its_index: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class IndexTable(NcFunction):
    class Meta:
        name = "index_table"

    its_index: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class KinematicStructure:
    class Meta:
        name = "kinematic_structure"

    joints: list[KinematicJoint] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class LimitationDefinitionSelect:
    class Meta:
        name = "limitation_definition_select"

    limits_and_fits: Optional[LimitsAndFits] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    plus_minus_bounds: Optional[PlusMinusBounds] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class LinearAxis(MachineToolAxis):
    class Meta:
        name = "linear_axis"

    minimum_range_of_motion: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_range_of_motion: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    displacement_error: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    repeatability_error: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    rapid_traverse_feed_rate: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    minimum_cutting_feed_rate: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_cutting_feed_rate: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_acceleration: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    maximum_deceleration: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    maximum_jerk: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class LoadTool(NcFunction):
    class Meta:
        name = "load_tool"

    its_tool: Optional[MachiningTool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class LocalTime:
    class Meta:
        name = "local_time"

    hour_component: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    minute_component: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    second_component: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    zone: Optional[CoordinatedUniversalTimeOffset] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Loop(TopologicalRepresentationItem):
    class Meta:
        name = "loop"


@dataclass
class MachineElementRelationship:
    class Meta:
        name = "machine_element_relationship"

    class_value: Optional[str] = field(
        default=None,
        metadata={
            "name": "class",
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    former_element: Optional[MachineToolElement] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    latter_element: Optional[MachineToolElement] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class MillingTechnology(Technology):
    class Meta:
        name = "milling_technology"

    cutspeed: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    spindle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    feedrate_per_tooth: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    synchronize_spindle_with_feed: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    inhibit_feedrate_override: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    inhibit_spindle_override: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_adaptive_control: Optional[AdaptiveControl] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class MultiLanguageString:
    class Meta:
        name = "multi_language_string"

    additional_language_string: list[StringWithLanguage] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    primary_language_string: Optional[StringWithLanguage] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class NonSequential(ProgramStructure):
    class Meta:
        name = "non_sequential"

    its_elements: list[Executable] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class NotExpression(UnaryBooleanExpression):
    class Meta:
        name = "not_expression"


@dataclass
class NumericalValue(ValueWithUnit):
    class Meta:
        name = "numerical_value"

    value_component: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class OptionalStop(NcFunction):
    class Meta:
        name = "optional_stop"


@dataclass
class OrExpression(MultipleArityBooleanExpression):
    class Meta:
        name = "or_expression"


@dataclass
class Parallel(ProgramStructure):
    class Meta:
        name = "parallel"

    branches: list[Executable] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class PersonOrganizationSelect:
    class Meta:
        name = "person_organization_select"

    organization: Optional[Organization] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    person_in_organization: Optional[PersonInOrganization] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Point(GeometricRepresentationItem):
    class Meta:
        name = "point"


@dataclass
class PositioningCapability:
    class Meta:
        name = "positioning_capability"

    maximum_range_of_motion: list[RangeOfMotion] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    maximum_displacement_error_of_linear_axis: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_repeatability_error_of_linear_axis: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ProductContext(ApplicationContextElement):
    class Meta:
        name = "product_context"

    discipline_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ProductDefinitionContext(ApplicationContextElement):
    class Meta:
        name = "product_definition_context"

    life_cycle_stage: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ProfileFloor:
    class Meta:
        name = "profile_floor"

    floor_radius: Optional[NumericParameter] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    start_or_end: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ProgramStop(NcFunction):
    class Meta:
        name = "program_stop"


@dataclass
class RectangularSize:
    class Meta:
        name = "rectangular_size"

    density: Optional[ValueWithUnit] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    height: Optional[ValueWithUnit] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    width: Optional[ValueWithUnit] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class RotaryAxis(MachineToolAxis):
    class Meta:
        name = "rotary_axis"

    displacement_angle_error: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    repeatability_angle_error: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    rapid_traverse_rotation_feed_rate: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    minimum_cutting_rotation_feed_rate: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_cutting_rotation_feed_rate: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_rotation_acceleration: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    maximum_rotation_deceleration: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    maximum_rotation_jerk: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Selective(ProgramStructure):
    class Meta:
        name = "selective"

    its_elements: list[Executable] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class SetMark(NcFunction):
    class Meta:
        name = "set_mark"


@dataclass
class ShapeRepresentation(Representation):
    class Meta:
        name = "shape_representation"


@dataclass
class Surface(GeometricRepresentationItem):
    class Meta:
        name = "surface"


@dataclass
class ToleranceSelect:
    class Meta:
        name = "tolerance_select"

    plus_minus_value: Optional[PlusMinusValue] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    limits_and_fits: Optional[LimitsAndFits] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ToolChanger(ToolHandlingUnit):
    class Meta:
        name = "tool_changer"

    spindle_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    cut_to_cut_min_tool_change_time: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    cut_to_cut_max_tool_change_time: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ToolMagazine(ToolHandlingUnit):
    class Meta:
        name = "tool_magazine"

    number_of_tools: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    random_access: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    diameter_full: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    diameter_empty: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    tool_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    tool_weight: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    storage_configuration: Optional[ToolStorageConfiguration] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    tool_magazine_contents: list[ToolAssembly] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ToolSpindle(Spindle):
    class Meta:
        name = "tool_spindle"

    spindle_tool_holder_style_designation: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    coolant_through_spindle: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class TurningTechnology(Technology):
    class Meta:
        name = "turning_technology"

    spindle_speed: Optional[SpeedSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    feed_per_revolution: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    sync_spindle_and_z_feed: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    inhibit_feedrate_override: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    inhibit_spindle_override: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_adaptive_control: Optional[AdaptiveControl] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Turret(ToolHandlingUnit):
    class Meta:
        name = "turret"

    spindle_name: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    number_of_fixed_tools: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    number_of_rotating_tools: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    cut_to_cut_min_turret_index_time: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    cut_to_cut_max_turret_index_time: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    turret_contents: list[ToolAssembly] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class UnloadTool(NcFunction):
    class Meta:
        name = "unload_tool"

    its_tool: Optional[MachiningTool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ValueLimit(ValueWithUnit):
    class Meta:
        name = "value_limit"

    limit: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    limit_qualifier: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ValueRange(ValueWithUnit):
    class Meta:
        name = "value_range"

    lower_limit: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    upper_limit: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class WaitForMark(NcFunction):
    class Meta:
        name = "wait_for_mark"

    its_channel: Optional[Channel] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class WhileStatement(ProgramStructure):
    class Meta:
        name = "while_statement"

    condition: Optional[BooleanExpression] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    body: Optional[Executable] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class WorkSpindle(Spindle):
    class Meta:
        name = "work_spindle"

    spindle_nose_designation: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    spindle_bore_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    round_bar_stock_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    through_hole_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    hex_bar_stock_capacity: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    chuck: Optional[Chuck] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class WorkTable(ElementCapability):
    class Meta:
        name = "work_table"

    rotatable: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    workpiece_weight: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    fixture_style: Optional[FixtureStyle] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    chuck: Optional[Chuck] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    t_slot: Optional[TSlot] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class XorExpression(BinaryBooleanExpression):
    class Meta:
        name = "xor_expression"


@dataclass
class AdvancedBrepShapeRepresentation(ShapeRepresentation):
    class Meta:
        name = "advanced_brep_shape_representation"


@dataclass
class ApproachRetractStrategy:
    class Meta:
        name = "approach_retract_strategy"

    tool_orientation: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Bidirectional(Two5DMillingStrategy):
    class Meta:
        name = "bidirectional"

    feed_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    stepover_direction: Optional[LeftOrRight] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_stroke_connection_strategy: Optional[StrokeConnectionStrategy] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class BidirectionalContour(Two5DMillingStrategy):
    class Meta:
        name = "bidirectional_contour"

    feed_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    stepover_direction: Optional[LeftOrRight] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    rotation_direction: Optional[RotDirection] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    spiral_cutmode: Optional[CutmodeType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class BidirectionalTurning(TurningMachiningStrategy):
    class Meta:
        name = "bidirectional_turning"

    feed_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    stepover_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    stepover_feed: Optional[FeedSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class BoundedCurve(Curve):
    class Meta:
        name = "bounded_curve"


@dataclass
class BoundedSurface(Surface):
    class Meta:
        name = "bounded_surface"


@dataclass
class CartesianPoint(Point):
    class Meta:
        name = "cartesian_point"

    coordinates: list[float] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "max_occurs": 3,
        },
    )


@dataclass
class CircularWorkTable(WorkTable):
    class Meta:
        name = "circular_work_table"

    table_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ComparisonEqual(ComparisonExpression):
    class Meta:
        name = "comparison_equal"


@dataclass
class ComparisonGreater(ComparisonExpression):
    class Meta:
        name = "comparison_greater"


@dataclass
class ComparisonGreaterEqual(ComparisonExpression):
    class Meta:
        name = "comparison_greater_equal"


@dataclass
class ComparisonLess(ComparisonExpression):
    class Meta:
        name = "comparison_less"


@dataclass
class ComparisonLessEqual(ComparisonExpression):
    class Meta:
        name = "comparison_less_equal"


@dataclass
class ComparisonNotEqual(ComparisonExpression):
    class Meta:
        name = "comparison_not_equal"


@dataclass
class ContinuousRotary(RotaryAxis):
    class Meta:
        name = "continuous_rotary"


@dataclass
class ContourBidirectional(Two5DMillingStrategy):
    class Meta:
        name = "contour_bidirectional"

    feed_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    stepover_direction: Optional[LeftOrRight] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    rotation_direction: Optional[RotDirection] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    spiral_cutmode: Optional[CutmodeType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ContourTurning(TurningMachiningStrategy):
    class Meta:
        name = "contour_turning"

    feed_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    back_path_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    lift_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    stepover_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    lift_height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    lift_feed: Optional[FeedSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    stepover_feed: Optional[FeedSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    variable_stepover_feed: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Coupling:
    class Meta:
        name = "coupling"

    coupling_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    pieces: Optional[NumericalValue] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    side: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    size: Optional[NumericalValue] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    style: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class DateAndTime:
    class Meta:
        name = "date_and_time"

    date_component: Optional[Date] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    time_component: Optional[LocalTime] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class DocumentContentProperty:
    class Meta:
        name = "document_content_property"

    detail_level: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    geometry_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    languages: list[Language] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    real_world_scale: Optional[NumericalValue] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class DocumentFormatProperty:
    class Meta:
        name = "document_format_property"

    character_code: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    data_format: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    size_format: Optional[RectangularSize] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class FaceBound(TopologicalRepresentationItem):
    class Meta:
        name = "face_bound"

    bound: Optional[Loop] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    orientation: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class GroovingStrategy(TurningMachiningStrategy):
    class Meta:
        name = "grooving_strategy"

    grooving_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    travel_distance: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Indexing(RotaryAxis):
    class Meta:
        name = "indexing"

    index_increment: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class LimitedSwing(RotaryAxis):
    class Meta:
        name = "limited_swing"

    minimum_angle_of_motion: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_angle_of_motion: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    axis_travel_limit: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class MachineToolRequirements(MachineTool):
    class Meta:
        name = "machine_tool_requirements"

    number_of_tools_in_tool_magazine: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    machining: list[MachiningCapability] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    spindles: list[SpindleCapability] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    positioning: Optional[PositioningCapability] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    axis: Optional[AxisCapability] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    touch_probing: Optional[MeasuringCapability] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    automatically_pallet_changeable: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class MachineToolSpecification(MachineTool):
    class Meta:
        name = "machine_tool_specification"

    machine_class: Optional[MachineClass] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    device_id: Optional[DeviceId] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    machining_capabilities: list[MachiningCapability] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    measuring_capability: Optional[MeasuringCapability] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    location: Optional[Locator] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    installation: Optional[Installation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    nc_controller_information: Optional[NcController] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    environment: Optional[EnvironmentalEvaluation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_elements: list[MachineToolElement] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class MillingMachineCuttingTool(MachiningTool):
    class Meta:
        name = "milling_machine_cutting_tool"

    its_cutting_edges: list[CuttingComponent] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    overall_assembly_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    effective_cutting_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_depth_of_cut: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    hand_of_cut: Optional[HandOfCutType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    coolant_through_tool: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class MillingMachineFunctions(MachineFunctions):
    class Meta:
        name = "milling_machine_functions"

    coolant: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    coolant_pressure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    mist: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    through_spindle_coolant: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    through_pressure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    axis_clamping: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    chip_removal: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    oriented_spindle_stop: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_process_model: Optional[ProcessModelList] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    other_functions: list[PropertyParameter] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Pallet(WorkTable):
    class Meta:
        name = "pallet"

    random_access: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    table_width: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    table_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    number_of_pallet: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    storage_configuration: Optional[PalletStorageConfiguration] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    pallet_change_time_minimum: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    pallet_change_time_maximum: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    pallet_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Pcurve(Curve):
    class Meta:
        name = "pcurve"

    basis_surface: Optional[Surface] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    reference_to_curve: Optional[DefinitionalRepresentation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PlaneCcStrategy(FreeformStrategy):
    class Meta:
        name = "plane_cc_strategy"

    its_plane_normal: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PlaneClStrategy(FreeformStrategy):
    class Meta:
        name = "plane_cl_strategy"

    its_plane_normal: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Product:
    class Meta:
        name = "product"

    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    frame_of_reference: list[ProductContext] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ProfileSelect:
    class Meta:
        name = "profile_select"

    through_profile_floor: Optional[ThroughProfileFloor] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    profile_floor: Optional[ProfileFloor] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class RectangularOffset:
    class Meta:
        name = "rectangular_offset"

    offset_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    offset_distance: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    row_index: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    column_index: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class RectangularWorkTable(WorkTable):
    class Meta:
        name = "rectangular_work_table"

    table_width: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    table_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Sensor(ElementCapability):
    class Meta:
        name = "sensor"

    device_id: Optional[DeviceId] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class StraightSpindle(ToolSpindle):
    class Meta:
        name = "straight_spindle"

    spindle_bore_depth: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    spindle_bore_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class StringSelect:
    class Meta:
        name = "string_select"

    default_language_string: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    multi_language_string: Optional[MultiLanguageString] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class TaperedSpindle(ToolSpindle):
    class Meta:
        name = "tapered_spindle"

    spindle_taper_designation: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ThreadedSpindle(ToolSpindle):
    class Meta:
        name = "threaded_spindle"

    spindle_thread_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    spindle_thread_pitch: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    spindle_thread_form: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ThreeAxesTiltedTool(ToolDirectionForMilling):
    class Meta:
        name = "three_axes_tilted_tool"

    its_tool_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class TolerancedLengthMeasure:
    class Meta:
        name = "toleranced_length_measure"

    theoretical_size: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    implicit_tolerance: Optional[ToleranceSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class TurningMachineFunctions(MachineFunctions):
    class Meta:
        name = "turning_machine_functions"

    coolant: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    coolant_type: Optional[CoolantSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    coolant_pressure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    axis_clamping: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    chip_removal: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    oriented_spindle_stop: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_process_model: Optional[ProcessModelList] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    other_functions: list[PropertyParameter] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    tail_stock: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    steady_rest: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    follow_rest: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Unidirectional(Two5DMillingStrategy):
    class Meta:
        name = "unidirectional"

    feed_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    cutmode: Optional[CutmodeType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class UnidirectionalTurning(TurningMachiningStrategy):
    class Meta:
        name = "unidirectional_turning"

    feed_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    back_path_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    lift_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    stepover_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    lift_height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    lift_feed: Optional[FeedSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    stepover_feed: Optional[FeedSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class UvStrategy(FreeformStrategy):
    class Meta:
        name = "uv_strategy"

    forward_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    sideward_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ValueLimitation:
    class Meta:
        name = "value_limitation"

    envelope: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    is_defined_by: Optional[LimitationDefinitionSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    limited_value: Optional[NumericalValue] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class AirStrategy(ApproachRetractStrategy):
    class Meta:
        name = "air_strategy"


@dataclass
class ApplicationContext13399:
    class Meta:
        name = "application_context_13399"

    application_domain: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class BSplineCurve(BoundedCurve):
    class Meta:
        name = "b_spline_curve"

    degree: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    control_points_list: list[CartesianPoint] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    curve_form: Optional[BSplineCurveForm] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    closed_curve: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    self_intersect: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ClassificationSystem:
    class Meta:
        name = "classification_system"

    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ConicalHoleBottom(BlindBottomCondition):
    class Meta:
        name = "conical_hole_bottom"

    tip_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    tip_radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class CurveWithNormalVector:
    class Meta:
        name = "curve_with_normal_vector"

    basiccurve: Optional[BoundedCurve] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    surface_normal: Optional[BoundedCurve] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class DiameterTaper:
    class Meta:
        name = "diameter_taper"

    final_diameter: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Document:
    class Meta:
        name = "document"

    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    name: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class DrillingCuttingTool(MillingMachineCuttingTool):
    class Meta:
        name = "drilling_cutting_tool"

    point_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Effectivity:
    class Meta:
        name = "effectivity"

    concerned_organization: list[Organization] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    effectivity_context: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    end_definition: Optional[DateTime] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    period: Optional[Duration] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    start_definition: Optional[DateTime] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    version_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ExternalLibraryReference:
    class Meta:
        name = "external_library_reference"

    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    external_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    library_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Face(TopologicalRepresentationItem):
    class Meta:
        name = "face"

    bounds: list[FaceBound] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class FlatSlotEndType(SlotEndType):
    class Meta:
        name = "flat_slot_end_type"

    corner_radius1: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    corner_radius2: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class FlatWithRadiusHoleBottom(BlindBottomCondition):
    class Meta:
        name = "flat_with_radius_hole_bottom"

    corner_radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class InProcessGeometry:
    class Meta:
        name = "in_process_geometry"

    as_is: Optional[AdvancedBrepShapeRepresentation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    to_be: Optional[AdvancedBrepShapeRepresentation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    removal: Optional[AdvancedBrepShapeRepresentation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Item:
    class Meta:
        name = "item"

    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    name: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class LeadingLineStrategy(FreeformStrategy):
    class Meta:
        name = "leading_line_strategy"

    its_line: Optional[BoundedCurve] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class MillingCuttingTool(MillingMachineCuttingTool):
    class Meta:
        name = "milling_cutting_tool"

    number_of_effective_teeth: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    edge_radius: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class MultistepGroovingStrategy(GroovingStrategy):
    class Meta:
        name = "multistep_grooving_strategy"

    retract_distance: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PartProbe(Sensor):
    class Meta:
        name = "part_probe"

    probe_type: Optional[ProbeType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    dimensionality: Optional[SensorDimensionality] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    setting_time: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Placement(GeometricRepresentationItem):
    class Meta:
        name = "placement"

    location: Optional[CartesianPoint] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PlungeStrategy(ApproachRetractStrategy):
    class Meta:
        name = "plunge_strategy"


@dataclass
class Polyline(BoundedCurve):
    class Meta:
        name = "polyline"

    points: list[CartesianPoint] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ProductDefinitionFormation:
    class Meta:
        name = "product_definition_formation"

    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    of_product: Optional[Product] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class RadiusedPocketBottomCondition(PocketBottomCondition):
    class Meta:
        name = "radiused_pocket_bottom_condition"

    floor_radius_center: Optional[CartesianPoint] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    floor_radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ReamingCuttingTool(MillingMachineCuttingTool):
    class Meta:
        name = "reaming_cutting_tool"

    taper_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class SphericalHoleBottom(BlindBottomCondition):
    class Meta:
        name = "spherical_hole_bottom"

    radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class StringValue(PropertyValue):
    class Meta:
        name = "string_value"

    value_specification: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class TappingCuttingTool(MillingMachineCuttingTool):
    class Meta:
        name = "tapping_cutting_tool"

    thread_form_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    thread_size: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    thread_pitch: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    taper_thread_count: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ToolBreakage(Sensor):
    class Meta:
        name = "tool_breakage"


@dataclass
class ToolProbing(TouchProbing):
    class Meta:
        name = "tool_probing"

    offset: Optional[CartesianPoint] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    max_wear: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_tool: Optional[MachiningTool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ToolSetting(Sensor):
    class Meta:
        name = "tool_setting"

    probe_type: Optional[ProbeType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    measuring_radius: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    measuring_length: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    measure_time: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class WoodruffSlotEndType(SlotEndType):
    class Meta:
        name = "woodruff_slot_end_type"

    radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ApRetractAngle(AirStrategy):
    class Meta:
        name = "ap_retract_angle"

    angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    travel_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ApRetractTangent(AirStrategy):
    class Meta:
        name = "ap_retract_tangent"

    radius: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Axis1Placement(Placement):
    class Meta:
        name = "axis1_placement"

    axis: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Axis2Placement3D(Placement):
    class Meta:
        name = "axis2_placement_3d"

    axis: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    ref_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ClassificationSourceSelect:
    class Meta:
        name = "classification_source_select"

    plib_class_reference: Optional[PlibClassReference] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document: Optional[Document] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    external_library_reference: Optional[ExternalLibraryReference] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ConnectedFaceSet(TopologicalRepresentationItem):
    class Meta:
        name = "connected_face_set"

    cfs_faces: list[Face] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class CurveWithSurfaceNormal:
    class Meta:
        name = "curve_with_surface_normal"

    bounded_pcurve: Optional[BoundedPcurve] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    curve_with_normal_vector: Optional[CurveWithNormalVector] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Din4000Reference(ExternalLibraryReference):
    class Meta:
        name = "din4000_reference"

    characteristics_code_no: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    part_no: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class DocumentTypeProperty:
    class Meta:
        name = "document_type_property"

    document_type_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    used_classification_system: Optional[ClassificationSystem] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class DocumentVersion:
    class Meta:
        name = "document_version"

    associated_document: Optional[Document] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class EffectivityRelationship:
    class Meta:
        name = "effectivity_relationship"

    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    related: Optional[Effectivity] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relating: Optional[Effectivity] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relation_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Endmill(MillingCuttingTool):
    class Meta:
        name = "endmill"

    tool_cutting_edge_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Facemill(MillingCuttingTool):
    class Meta:
        name = "facemill"

    tool_cutting_edge_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class GeneralProfileFloor(ProfileFloor):
    class Meta:
        name = "general_profile_floor"

    floor: Optional[Face] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ItemVersion:
    class Meta:
        name = "item_version"

    associated_item: Optional[Item] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class NamedSize(RectangularSize):
    class Meta:
        name = "named_size"

    referenced_standard: Optional[ClassificationSystem] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    size: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PhysicalItem(Item):
    class Meta:
        name = "physical_item"


@dataclass
class PlungeHelix(PlungeStrategy):
    class Meta:
        name = "plunge_helix"

    radius: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PlungeRamp(PlungeStrategy):
    class Meta:
        name = "plunge_ramp"

    angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PlungeToolaxis(PlungeStrategy):
    class Meta:
        name = "plunge_toolaxis"


@dataclass
class PlungeZigzag(PlungeStrategy):
    class Meta:
        name = "plunge_zigzag"

    angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    width: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ProductDefinition:
    class Meta:
        name = "product_definition"

    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    formation: Optional[ProductDefinitionFormation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    frame_of_reference: Optional[ProductDefinitionContext] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PropertySourceSelect:
    class Meta:
        name = "property_source_select"

    plib_property_reference: Optional[PlibPropertyReference] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    external_library_reference: Optional[ExternalLibraryReference] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document: Optional[Document] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class SpecificItemClassification:
    class Meta:
        name = "specific_item_classification"

    associated_item: list[Item] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    classification_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Spotdrill(DrillingCuttingTool):
    class Meta:
        name = "spotdrill"


@dataclass
class TaperSelect:
    class Meta:
        name = "taper_select"

    diameter_taper: Optional[DiameterTaper] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    angle_taper: Optional[AngleTaper] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ToolLengthProbing(ToolProbing):
    class Meta:
        name = "tool_length_probing"


@dataclass
class ToolRadiusProbing(ToolProbing):
    class Meta:
        name = "tool_radius_probing"


@dataclass
class ToolpathSpeed:
    class Meta:
        name = "toolpath_speed"

    speed: Optional[BSplineCurve] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class TwistDrill(DrillingCuttingTool):
    class Meta:
        name = "twist_drill"


@dataclass
class AssignedDocumentSelect:
    class Meta:
        name = "assigned_document_select"

    document_version: Optional[DocumentVersion] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document: Optional[Document] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Block(GeometricRepresentationItem):
    class Meta:
        name = "block"

    position: Optional[Axis2Placement3D] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    x: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    y: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    z: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class DocumentFile:
    class Meta:
        name = "document_file"

    content: Optional[DocumentContentProperty] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    creation: Optional[DocumentCreationProperty] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document_file_type: Optional[DocumentTypeProperty] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    external_id_and_location: list[ExternalFileIdAndLocation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    file_format: Optional[DocumentFormatProperty] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    file_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    size: Optional[DocumentSizeProperty] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    version_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class DocumentRepresentation:
    class Meta:
        name = "document_representation"

    associated_document_version: Optional[DocumentVersion] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    common_location: list[DocumentLocationProperty] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    content: Optional[DocumentContentProperty] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    creation: Optional[DocumentCreationProperty] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    representation_format: Optional[DocumentFormatProperty] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    size: Optional[DocumentSizeProperty] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class DocumentVersionRelationship:
    class Meta:
        name = "document_version_relationship"

    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    related: Optional[DocumentVersion] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relating: Optional[DocumentVersion] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relation_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ElementarySurface(Surface):
    class Meta:
        name = "elementary_surface"

    position: Optional[Axis2Placement3D] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class GeneralClassification:
    class Meta:
        name = "general_classification"

    classification_source: Optional[ClassificationSourceSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    used_classification_system: Optional[ClassificationSystem] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    version_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ItemDefinition:
    class Meta:
        name = "item_definition"

    additional_context: list[ApplicationContext] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    associated_item_version: Optional[ItemVersion] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    initial_context: Optional[ApplicationContext] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    name: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ItemVersionRelationship:
    class Meta:
        name = "item_version_relationship"

    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    related: Optional[ItemVersion] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relating: Optional[ItemVersion] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relation_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class OpenShell(ConnectedFaceSet):
    class Meta:
        name = "open_shell"


@dataclass
class PartialAreaDefinition:
    class Meta:
        name = "partial_area_definition"

    effective_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    placement: Optional[Axis2Placement3D] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class PhysicalItemVersion(ItemVersion):
    class Meta:
        name = "physical_item_version"


@dataclass
class ProductDefinitionRelationship:
    class Meta:
        name = "product_definition_relationship"

    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    relating_product_definition: Optional[ProductDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    related_product_definition: Optional[ProductDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Profile:
    class Meta:
        name = "profile"

    placement: Optional[Axis2Placement3D] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Property:
    class Meta:
        name = "property"

    allowed_unit: list[Unit] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    property_source: Optional[PropertySourceSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    property_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    version_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class RealizedItemAssociation:
    class Meta:
        name = "realized_item_association"

    physical_item: Optional[PhysicalItem] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    realized_item: Optional[Item] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class RightCircularCylinder(GeometricRepresentationItem):
    class Meta:
        name = "right_circular_cylinder"

    position: Optional[Axis1Placement] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    radius: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class SpecificItemClassificationHierarchy:
    class Meta:
        name = "specific_item_classification_hierarchy"

    sub_classification: Optional[SpecificItemClassification] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    super_classification: Optional[SpecificItemClassification] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ToolpathSpeedprofile:
    class Meta:
        name = "toolpath_speedprofile"

    toolpath_speed: Optional[ToolpathSpeed] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    positive_ratio_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    speed_name: Optional[SpeedName] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class TravelPath:
    class Meta:
        name = "travel_path"

    placement: Optional[Axis2Placement3D] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class AssemblyDefinition(ItemDefinition):
    class Meta:
        name = "assembly_definition"


@dataclass
class BoundingGeometrySelect:
    class Meta:
        name = "bounding_geometry_select"

    block: Optional[Block] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    right_circular_cylinder: Optional[RightCircularCylinder] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    advanced_brep_shape_representation: Optional[AdvancedBrepShapeRepresentation] = (
        field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://digital-thread.re/dt_asset",
            },
        )
    )


@dataclass
class CharacterizedProductDefinition:
    class Meta:
        name = "characterized_product_definition"

    product_definition: Optional[ProductDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    product_definition_relationship: Optional[ProductDefinitionRelationship] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class CircularPath(TravelPath):
    class Meta:
        name = "circular_path"

    radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ClosedProfile(Profile):
    class Meta:
        name = "closed_profile"


@dataclass
class DigitalFile(DocumentFile):
    class Meta:
        name = "digital_file"


@dataclass
class GeneralClassificationHierarchy:
    class Meta:
        name = "general_classification_hierarchy"

    sub_classification: Optional[GeneralClassification] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    super_classification: Optional[GeneralClassification] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class GeneralPath(TravelPath):
    class Meta:
        name = "general_path"

    swept_path: Optional[BoundedCurve] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ItemDefinitionRelationship:
    class Meta:
        name = "item_definition_relationship"

    related: Optional[ItemDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relating: Optional[ItemDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relation_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ItemInstance:
    class Meta:
        name = "item_instance"

    definition: Optional[ItemDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class LinearPath(TravelPath):
    class Meta:
        name = "linear_path"

    distance: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class MatingDefinition(ItemDefinition):
    class Meta:
        name = "mating_definition"

    mating_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class OpenProfile(Profile):
    class Meta:
        name = "open_profile"


@dataclass
class PhysicalFile(DocumentFile):
    class Meta:
        name = "physical_file"


@dataclass
class PhysicalItemDefinition(ItemDefinition):
    class Meta:
        name = "physical_item_definition"


@dataclass
class Plane(ElementarySurface):
    class Meta:
        name = "plane"


@dataclass
class PropertyRelationship:
    class Meta:
        name = "property_relationship"

    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    related: Optional[Property] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relating: Optional[Property] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relation_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PropertyValueRepresentation:
    class Meta:
        name = "property_value_representation"

    definition: Optional[Property] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    global_unit: Optional[Unit] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    qualifier: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    specified_value: Optional[PropertyValue] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    value_determination: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Toolpath:
    class Meta:
        name = "toolpath"

    its_priority: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_type: Optional[ToolpathType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_speed: Optional[ToolpathSpeedprofile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_technology: Optional[Technology] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_machine_functions: Optional[MachineFunctions] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Workingstep(Executable):
    class Meta:
        name = "workingstep"

    its_secplane: Optional[ElementarySurface] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class CharacterizedDefinition:
    class Meta:
        name = "characterized_definition"

    characterized_object: Optional[CharacterizedObject] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    characterized_product_definition: Optional[CharacterizedProductDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    shape_definition: Optional[ShapeDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class CircularClosedProfile(ClosedProfile):
    class Meta:
        name = "circular_closed_profile"

    diameter: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ClassificationAttribute:
    class Meta:
        name = "classification_attribute"

    allowed_value: list[PropertyValueRepresentation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    associated_classification: Optional[GeneralClassification] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    attribute_definition: Optional[Property] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    name: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class CompleteCircularPath(CircularPath):
    class Meta:
        name = "complete_circular_path"


@dataclass
class DigitalDocument(DocumentRepresentation):
    class Meta:
        name = "digital_document"

    file: list[DigitalFile] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ExternalModel:
    class Meta:
        name = "external_model"

    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    is_defined_as: Optional[DigitalFile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    is_defined_in: Optional[CartesianCoordinateSpace] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    model_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Feedstop(Toolpath):
    class Meta:
        name = "feedstop"

    dwell: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class GeneralClosedProfile(ClosedProfile):
    class Meta:
        name = "general_closed_profile"

    closed_profile_shape: Optional[BoundedCurve] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class GeneralProfile(OpenProfile):
    class Meta:
        name = "general_profile"

    its_profile: Optional[BoundedCurve] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class LinearProfile(OpenProfile):
    class Meta:
        name = "linear_profile"

    profile_length: Optional[NumericParameter] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class NgonProfile(ClosedProfile):
    class Meta:
        name = "ngon_profile"

    diameter: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    number_of_sides: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    circumscribed_or_across_flats: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ParameterisedPath(Toolpath):
    class Meta:
        name = "parameterised_path"


@dataclass
class PartialCircularPath(CircularPath):
    class Meta:
        name = "partial_circular_path"

    sweep_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PartialCircularProfile(OpenProfile):
    class Meta:
        name = "partial_circular_profile"

    radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    sweep_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PhysicalDocument(DocumentRepresentation):
    class Meta:
        name = "physical_document"

    file: list[PhysicalFile] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class PhysicalItemLocationAssociation:
    class Meta:
        name = "physical_item_location_association"

    located_item: Optional[PhysicalItemDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    location: Optional[Location] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PhysicalItemStateAssociation:
    class Meta:
        name = "physical_item_state_association"

    associated_physical_item: Optional[PhysicalItemDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    associated_state: Optional[State] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    role: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PhysicalItemStructureAssociation:
    class Meta:
        name = "physical_item_structure_association"

    related: Optional[PhysicalItemDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relating: Optional[PhysicalItemDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PlanarProfileFloor(ProfileFloor):
    class Meta:
        name = "planar_profile_floor"

    floor: Optional[Plane] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ProfiledCorner:
    class Meta:
        name = "profiled_corner"

    transition_profile: Optional[OpenProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PropertyValueRepresentationRelationship:
    class Meta:
        name = "property_value_representation_relationship"

    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    related: Optional[PropertyValueRepresentation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relating: Optional[PropertyValueRepresentation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relation_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class QuantifiedInstance(ItemInstance):
    class Meta:
        name = "quantified_instance"

    quantity: Optional[NumericalValue] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class RectangularClosedProfile(ClosedProfile):
    class Meta:
        name = "rectangular_closed_profile"

    profile_width: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    profile_length: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class RestrictedAreaSelect:
    class Meta:
        name = "restricted_area_select"

    bounded_surface: Optional[BoundedSurface] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    bounding_geometry_select: Optional[BoundingGeometrySelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class RoundedUProfile(OpenProfile):
    class Meta:
        name = "rounded_u_profile"

    width: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class SquareUProfile(OpenProfile):
    class Meta:
        name = "square_u_profile"

    width: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    first_radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    first_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    second_radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    second_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class TeeProfile(OpenProfile):
    class Meta:
        name = "tee_profile"

    first_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    second_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    cross_bar_width: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    cross_bar_depth: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    width: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    first_offset: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    second_offset: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ToolpathList:
    class Meta:
        name = "toolpath_list"

    its_list: list[Toolpath] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Trajectory(Toolpath):
    class Meta:
        name = "trajectory"

    its_direction: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class VeeProfile(OpenProfile):
    class Meta:
        name = "vee_profile"

    profile_radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    profile_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    tilt_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Workpiece:
    class Meta:
        name = "workpiece"

    its_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_material: Optional[Material] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    global_tolerance: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_rawpiece: Optional["Workpiece"] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_geometry: Optional[AdvancedBrepShapeRepresentation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_bounding_geometry: Optional[BoundingGeometrySelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    clamping_positions: list[CartesianPoint] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    ref_dt_material: Optional[DtReference] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Operation:
    class Meta:
        name = "OPERATION"

    its_toolpath: Optional[ToolpathList] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_tool_direction: Optional[ToolDirection] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    ref_dt_cutting_tool: Optional[DtReference] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class AliasSelect:
    class Meta:
        name = "alias_select"

    item: Optional[Item] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item_version: Optional[ItemVersion] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item_definition: Optional[ItemDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    property: Optional[Property] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    grade: Optional[Grade] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    classification_attribute: Optional[ClassificationAttribute] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    classification_system: Optional[ClassificationSystem] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document: Optional[Document] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document_representation: Optional[DocumentRepresentation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document_version: Optional[DocumentVersion] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    general_classification: Optional[GeneralClassification] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item_instance: Optional[ItemInstance] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    organization: Optional[Organization] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document_type_property: Optional[DocumentTypeProperty] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class AlongPath(ApproachRetractStrategy):
    class Meta:
        name = "along_path"

    path: Optional[ToolpathList] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ApproachLiftPath(ParameterisedPath):
    class Meta:
        name = "approach_lift_path"

    fix_point: Optional[CartesianPoint] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    fix_point_dir: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class AxisTrajectory(Trajectory):
    class Meta:
        name = "axis_trajectory"

    axis_list: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    commands: list[BoundedCurve] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Connector(ParameterisedPath):
    class Meta:
        name = "connector"


@dataclass
class CornerTransitionSelect:
    class Meta:
        name = "corner_transition_select"

    chamfered_corner: Optional[ChamferedCorner] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    rounded_corner: Optional[RoundedCorner] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    profiled_corner: Optional[ProfiledCorner] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class CutterContactTrajectory(Trajectory):
    class Meta:
        name = "cutter_contact_trajectory"

    basiccurve: Optional[CurveWithSurfaceNormal] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_toolaxis: Optional[BoundedCurve] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_contact_type: Optional[ContactType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class CutterLocationTrajectory(Trajectory):
    class Meta:
        name = "cutter_location_trajectory"

    basiccurve: Optional[BoundedCurve] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_toolaxis: Optional[BoundedCurve] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    surface_normal: Optional[BoundedCurve] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ExternalGeometricModel(ExternalModel):
    class Meta:
        name = "external_geometric_model"

    model_extent: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ExternalPicture(ExternalModel):
    class Meta:
        name = "external_picture"


@dataclass
class GeometricModelRelationshipWithTransformation:
    class Meta:
        name = "geometric_model_relationship_with_transformation"

    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    model_placement: Optional[Transformation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    related: Optional[ExternalModel] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relating: Optional[ExternalModel] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relation_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PropertyDefinition:
    class Meta:
        name = "property_definition"

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    definition: Optional[CharacterizedDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class WorkpieceCompleteProbing(TouchProbing):
    class Meta:
        name = "workpiece_complete_probing"

    its_workpiece: Optional[Workpiece] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    probing_distance: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_probe: Optional[TouchProbe] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    computed_offset: Optional[OffsetVector] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class WorkpieceFeature:
    class Meta:
        name = "workpiece_feature"

    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    representation: list[ExternalModel] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class WorkpieceProbing(TouchProbing):
    class Meta:
        name = "workpiece_probing"

    start_position: Optional[Axis2Placement3D] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_workpiece: Optional[Workpiece] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    expected_value: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_probe: Optional[TouchProbe] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class WorkpieceSetup:
    class Meta:
        name = "workpiece_setup"

    its_workpiece: Optional[Workpiece] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_origin: Optional[Axis2Placement3D] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_offset: Optional[OffsetVector] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_restricted_area: Optional[RestrictedAreaSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_instructions: list[SetupInstruction] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class AliasIdentification:
    class Meta:
        name = "alias_identification"

    alias_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    alias_scope: Optional[Organization] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    alias_version_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    is_applied_to: Optional[AliasSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ApLiftPathAngle(ApproachLiftPath):
    class Meta:
        name = "ap_lift_path_angle"

    angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    benddist: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ApLiftPathTangent(ApproachLiftPath):
    class Meta:
        name = "ap_lift_path_tangent"

    radius: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ConnectDirect(Connector):
    class Meta:
        name = "connect_direct"


@dataclass
class ConnectSecplane(Connector):
    class Meta:
        name = "connect_secplane"

    up_dir: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    down_dir: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class CornerTransition:
    class Meta:
        name = "corner_transition"

    corner_identity: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    transition: Optional[CornerTransitionSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ItemCharacteristicSelect:
    class Meta:
        name = "item_characteristic_select"

    cutting_condition: Optional[CuttingCondition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    coupling: Optional[Coupling] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    workpiece_feature: Optional[WorkpieceFeature] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    material_designation: Optional[MaterialDesignation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    cutting_data_association: Optional[CuttingDataAssociation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    grade: Optional[Grade] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ItemStructureAssociation:
    class Meta:
        name = "item_structure_association"

    placement: Optional[GeometricModelRelationshipWithTransformation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    related: Optional[ItemInstance] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relating: Optional[ItemDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class KinematicPropertyDefinition(PropertyDefinition):
    class Meta:
        name = "kinematic_property_definition"

    ground_definition: Optional[CharacterizedDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class MachiningOperation(Operation):
    class Meta:
        name = "machining_operation"

    its_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    erretract_plane: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    start_point: Optional[CartesianPoint] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_tool: Optional[MachiningTool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_technology: Optional[Technology] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_machine_functions: Optional[MachineFunctions] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ProductDefinitionShape(PropertyDefinition):
    class Meta:
        name = "product_definition_shape"


@dataclass
class Setup:
    class Meta:
        name = "setup"

    its_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_origin: Optional[Axis2Placement3D] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_secplane: Optional[ElementarySurface] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_workpiece_setup: list[WorkpieceSetup] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class AssemblyAssociation(ItemStructureAssociation):
    class Meta:
        name = "assembly_association"


@dataclass
class CuttingEdgeProperties:
    class Meta:
        name = "cutting_edge_properties"

    expected_tool_life: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_technology: Optional[Technology] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    cutting_edge_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    tool_cutting_edge_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    tool_cutting_edge_angle_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    tool_included_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    corner_transitions: list[CornerTransition] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    maximum_side_cutting_depth: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    maximum_end_cutting_depth: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ItemCharacteristicAssociation:
    class Meta:
        name = "item_characteristic_association"

    associated_characteristic: Optional[ItemCharacteristicSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    associated_item: Optional[ItemDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ManufacturingFeature:
    class Meta:
        name = "manufacturing_feature"

    its_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_workpiece: Optional[Workpiece] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_operations: list[MachiningOperation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class MatingAssociation(ItemStructureAssociation):
    class Meta:
        name = "mating_association"


@dataclass
class Mechanism:
    class Meta:
        name = "mechanism"

    structure_definition: Optional[KinematicStructure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    base: Optional[KinematicLink] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    containing_property: Optional[KinematicPropertyDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class MillingMachiningOperation(MachiningOperation):
    class Meta:
        name = "milling_machining_operation"

    overcut_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ShapeAspect:
    class Meta:
        name = "shape_aspect"

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    of_shape: Optional[ProductDefinitionShape] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    product_definitional: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class TurningMachiningOperation(MachiningOperation):
    class Meta:
        name = "turning_machining_operation"

    approach: Optional[ApproachRetractStrategy] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    retract: Optional[ApproachRetractStrategy] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_machining_strategy: Optional[TurningMachiningStrategy] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Workplan(ProgramStructure):
    class Meta:
        name = "workplan"

    its_elements: list[Executable] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_channel: Optional[Channel] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_setup: Optional[Setup] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_effect: Optional[InProcessGeometry] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    ref_dt_machine_tool: Optional[DtReference] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    ref_dt_nc_file: list[DtReference] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    ref_dt_tdms_file: list[DtReference] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    ref_dt_vm_file: list[DtReference] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Contouring(TurningMachiningOperation):
    class Meta:
        name = "contouring"

    allowance: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class DrillingTypeOperation(MillingMachiningOperation):
    class Meta:
        name = "drilling_type_operation"

    cutting_depth: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    previous_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    dwell_time_bottom: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    feed_on_retract: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_machining_strategy: Optional[DrillingTypeStrategy] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class DtProject(DtElement):
    class Meta:
        name = "dt_project"

    its_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    main_workplan: Optional[Workplan] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_workpieces: list[Workpiece] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_owner: Optional[PersonAndAddress] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_release: Optional[DateAndTime] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_status: Optional[Approval] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Facing(TurningMachiningOperation):
    class Meta:
        name = "facing"

    allowance: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Grooving(TurningMachiningOperation):
    class Meta:
        name = "grooving"

    dwell: Optional[DwellSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    allowance: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Knurling(TurningMachiningOperation):
    class Meta:
        name = "knurling"


@dataclass
class MachineKinematicAssociation:
    class Meta:
        name = "machine_kinematic_association"

    machine: Optional[MachineToolSpecification] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    kinematics: Optional[Mechanism] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class MachiningWorkingstep(Workingstep):
    class Meta:
        name = "machining_workingstep"

    its_feature: Optional[ManufacturingFeature] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_operation: Optional[MachiningOperation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_effect: Optional[InProcessGeometry] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class MatedItemRelationship:
    class Meta:
        name = "mated_item_relationship"

    mating_material: list[QuantifiedInstance] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    related: Optional[MatingAssociation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relating: Optional[MatingAssociation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class MillingTypeOperation(MillingMachiningOperation):
    class Meta:
        name = "milling_type_operation"

    approach: Optional[ApproachRetractStrategy] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    retract: Optional[ApproachRetractStrategy] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Project:
    class Meta:
        name = "project"

    its_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    main_workplan: Optional[Workplan] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_workpieces: list[Workpiece] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_owner: Optional[PersonAndAddress] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_release: Optional[DateAndTime] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_status: Optional[Approval] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Region(ManufacturingFeature):
    class Meta:
        name = "region"

    feature_placement: Optional[Axis2Placement3D] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ShapeAspectRelationship:
    class Meta:
        name = "shape_aspect_relationship"

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    relating_shape_aspect: Optional[ShapeAspect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    related_shape_aspect: Optional[ShapeAspect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Threading(TurningMachiningOperation):
    class Meta:
        name = "threading"

    allowance: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class TurningMachineCuttingTool(MachiningTool):
    class Meta:
        name = "turning_machine_cutting_tool"

    functional_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    f_dimension: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    minimum_cutting_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    a_dimension_on_f: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    a_dimension_on_lf: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    cutting_edge: Optional[CuttingEdgeProperties] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    hand_of_tool: Optional[HandOfToolType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class TurningWorkingstep(Workingstep):
    class Meta:
        name = "turning_workingstep"

    its_features: list[ManufacturingFeature] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_operation: Optional[TurningMachiningOperation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_effect: Optional[InProcessGeometry] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Two5DManufacturingFeature(ManufacturingFeature):
    class Meta:
        name = "two5D_manufacturing_feature"

    feature_placement: Optional[Axis2Placement3D] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class WorkplanPhysicalResourceAssociation:
    class Meta:
        name = "workplan_physical_resource_association"

    workplan_of_resource: Optional[Workplan] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    physical_resource: Optional[MachineToolRequirements] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class BackBoring(DrillingTypeOperation):
    class Meta:
        name = "back_boring"


@dataclass
class BoringOperation(DrillingTypeOperation):
    class Meta:
        name = "boring_operation"

    spindle_stop_at_bottom: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    depth_of_testcut: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    waiting_position: Optional[CartesianPoint] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ContouringFinish(Contouring):
    class Meta:
        name = "contouring_finish"


@dataclass
class ContouringRough(Contouring):
    class Meta:
        name = "contouring_rough"


@dataclass
class CuttingIn(Grooving):
    class Meta:
        name = "cutting_in"


@dataclass
class DocumentedElementSelect:
    class Meta:
        name = "documented_element_select"

    item: Optional[Item] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item_version: Optional[ItemVersion] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    classification_attribute: Optional[ClassificationAttribute] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    classification_system: Optional[ClassificationSystem] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item_definition: Optional[ItemDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    general_classification: Optional[GeneralClassification] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item_structure_association: Optional[ItemStructureAssociation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item_instance: Optional[ItemInstance] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    organization: Optional[Organization] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    person: Optional[Person] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    property: Optional[Property] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    specific_item_classification: Optional[SpecificItemClassification] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    material_designation: Optional[MaterialDesignation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    mated_item_relationship: Optional[MatedItemRelationship] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    physical_item_structure_association: Optional[PhysicalItemStructureAssociation] = (
        field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://digital-thread.re/dt_asset",
            },
        )
    )


@dataclass
class DrillingOperation(DrillingTypeOperation):
    class Meta:
        name = "drilling_operation"


@dataclass
class FacingFinish(Facing):
    class Meta:
        name = "facing_finish"


@dataclass
class FacingRough(Facing):
    class Meta:
        name = "facing_rough"


@dataclass
class FreeformOperation(MillingTypeOperation):
    class Meta:
        name = "freeform_operation"

    its_machining_strategy: Optional[FreeformStrategy] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class GeneralPocketBottomCondition(PocketBottomCondition):
    class Meta:
        name = "general_pocket_bottom_condition"

    shape: Optional[Region] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class GeneralTurningTool(TurningMachineCuttingTool):
    class Meta:
        name = "general_turning_tool"


@dataclass
class GroovingFinish(Grooving):
    class Meta:
        name = "grooving_finish"


@dataclass
class GroovingRough(Grooving):
    class Meta:
        name = "grooving_rough"


@dataclass
class GroovingTool(TurningMachineCuttingTool):
    class Meta:
        name = "grooving_tool"

    cutting_width: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    maximum_grooving_depth: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    corner_radius: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    maximum_axial_grooving_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    minimum_axial_grooving_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ItemPropertySelect:
    class Meta:
        name = "item_property_select"

    item_definition: Optional[ItemDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item_characteristic_select: Optional[ItemCharacteristicSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document_file: Optional[DocumentFile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document_representation: Optional[DocumentRepresentation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item_structure_association: Optional[ItemStructureAssociation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item_instance: Optional[ItemInstance] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    mated_item_relationship: Optional[MatedItemRelationship] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    physical_item_structure_association: Optional[PhysicalItemStructureAssociation] = (
        field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://digital-thread.re/dt_asset",
            },
        )
    )


@dataclass
class MachiningFeature(Two5DManufacturingFeature):
    class Meta:
        name = "machining_feature"

    depth: Optional[ElementarySurface] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ProjectPhysicalResourceAssociation:
    class Meta:
        name = "project_physical_resource_association"

    project_of_resource: Optional[Project] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    physical_resource: Optional[MachineToolRequirements] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class RegionProjection(Region):
    class Meta:
        name = "region_projection"

    proj_curve: Optional[BoundedCurve] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    proj_dir: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    depth: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class RegionSurfaceList(Region):
    class Meta:
        name = "region_surface_list"

    surface_list: list[BoundedSurface] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ReplicateFeature(Two5DManufacturingFeature):
    class Meta:
        name = "replicate_feature"

    replicate_base_feature: Optional[Two5DManufacturingFeature] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Tapping(DrillingTypeOperation):
    class Meta:
        name = "tapping"

    compensation_chuck: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ThreadDrilling(DrillingTypeOperation):
    class Meta:
        name = "thread_drilling"

    helical_movement_on_forward: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ThreadingFinish(Threading):
    class Meta:
        name = "threading_finish"


@dataclass
class ThreadingRough(Threading):
    class Meta:
        name = "threading_rough"


@dataclass
class TurningFeature(Two5DManufacturingFeature):
    class Meta:
        name = "turning_feature"


@dataclass
class TurningThreadingTool(TurningMachineCuttingTool):
    class Meta:
        name = "turning_threading_tool"

    threading_pitch: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    thread_hand: Optional[ThreadHandType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_thread_type: Optional[ThreadType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    thread_profile: Optional[ThreadProfileType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    thread_form_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Two5DMillingOperation(MillingTypeOperation):
    class Meta:
        name = "two5D_milling_operation"

    its_machining_strategy: Optional[Two5DMillingStrategy] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class UserDefinedTurningTool(TurningMachineCuttingTool):
    class Meta:
        name = "user_defined_turning_tool"

    identifier: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Boring(BoringOperation):
    class Meta:
        name = "boring"


@dataclass
class Boss(MachiningFeature):
    class Meta:
        name = "boss"

    its_boundary: Optional[ClosedProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    slope: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class BottomAndSideMilling(Two5DMillingOperation):
    class Meta:
        name = "bottom_and_side_milling"

    axial_cutting_depth: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    radial_cutting_depth: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    allowance_side: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    allowance_bottom: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class CenterDrilling(DrillingOperation):
    class Meta:
        name = "center_drilling"


@dataclass
class CircularPattern(ReplicateFeature):
    class Meta:
        name = "circular_pattern"

    angle_increment: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    number_of_feature: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relocated_base_feature: list[CircularOffset] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    missing_base_feature: list[CircularOmit] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    base_feature_diameter: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    base_feature_rotation: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class CounterSinking(DrillingOperation):
    class Meta:
        name = "counter_sinking"


@dataclass
class DocumentAssignment:
    class Meta:
        name = "document_assignment"

    assigned_document: Optional[AssignedDocumentSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    is_assigned_to: Optional[DocumentedElementSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    role: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Drilling(DrillingOperation):
    class Meta:
        name = "drilling"


@dataclass
class GeneralPattern(ReplicateFeature):
    class Meta:
        name = "general_pattern"

    replicate_locations: list[Axis2Placement3D] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Knurl(TurningFeature):
    class Meta:
        name = "knurl"

    base_feature: Optional[TurningFeature] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    partial_profile: Optional[PartialAreaDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    tooth_depth: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    diametral_pitch: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    root_fillet: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    number_of_teeth: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    major_diameter: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    nominal_diameter: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class MachinedSurface:
    class Meta:
        name = "machined_surface"

    its_machining_feature: Optional[MachiningFeature] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    surface_element: Optional[BottomOrSide] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class MultistepDrilling(DrillingOperation):
    class Meta:
        name = "multistep_drilling"

    retract_distance: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    first_depth: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    depth_of_step: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    dwell_time_step: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class OuterRound(TurningFeature):
    class Meta:
        name = "outer_round"


@dataclass
class PlaneMilling(Two5DMillingOperation):
    class Meta:
        name = "plane_milling"

    axial_cutting_depth: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    allowance_bottom: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ProfileFeature(MachiningFeature):
    class Meta:
        name = "profile_feature"

    profile_swept_shape: Optional[LinearPath] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PropertyValueAssociation:
    class Meta:
        name = "property_value_association"

    definitional: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    described_element: Optional[ItemPropertySelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    describing_property_value: Optional[PropertyValueRepresentation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    validity_context: Optional[Organization] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Reaming(BoringOperation):
    class Meta:
        name = "reaming"


@dataclass
class RectangularPattern(ReplicateFeature):
    class Meta:
        name = "rectangular_pattern"

    spacing: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    its_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    number_of_rows: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    number_of_columns: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    row_spacing: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    row_layout_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    relocated_base_feature: list[RectangularOffset] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    missing_base_feature: list[RectangularOmit] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class RevolvedFeature(TurningFeature):
    class Meta:
        name = "revolved_feature"

    material_side: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    radius: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class RoundHole(MachiningFeature):
    class Meta:
        name = "round_hole"

    diameter: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    change_in_diameter: Optional[TaperSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    bottom_condition: Optional[HoleBottomCondition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class RoundedEnd(MachiningFeature):
    class Meta:
        name = "rounded_end"

    course_of_travel: Optional[LinearPath] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    partial_circular_boundary: Optional[PartialCircularProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class SideMilling(Two5DMillingOperation):
    class Meta:
        name = "side_milling"

    axial_cutting_depth: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    radial_cutting_depth: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    allowance_side: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class Slot(MachiningFeature):
    class Meta:
        name = "slot"

    course_of_travel: Optional[TravelPath] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    swept_shape: Optional[OpenProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    end_conditions: list[SlotEndType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "max_occurs": 2,
        },
    )


@dataclass
class SphericalCap(MachiningFeature):
    class Meta:
        name = "spherical_cap"

    internal_angle: Optional[NumericParameter] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    radius: Optional[NumericParameter] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Thread(MachiningFeature):
    class Meta:
        name = "thread"

    partial_profile: Optional[PartialAreaDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    applied_shape: list[MachiningFeature] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    inner_or_outer_thread: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    qualifier: Optional[DescriptiveParameter] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    fit_class: Optional[DescriptiveParameter] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    form: Optional[DescriptiveParameter] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    major_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    number_of_threads: Optional[NumericParameter] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    thread_hand: Optional[DescriptiveParameter] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ToolpathFeature(MachiningFeature):
    class Meta:
        name = "toolpath_feature"


@dataclass
class TransitionFeature(ManufacturingFeature):
    class Meta:
        name = "transition_feature"

    first_feature: Optional[MachiningFeature] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    second_feature: Optional[MachiningFeature] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class BottomAndSideFinishMilling(BottomAndSideMilling):
    class Meta:
        name = "bottom_and_side_finish_milling"


@dataclass
class BottomAndSideRoughMilling(BottomAndSideMilling):
    class Meta:
        name = "bottom_and_side_rough_milling"


@dataclass
class CatalogueThread(Thread):
    class Meta:
        name = "catalogue_thread"

    documentation: Optional[Specification] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Chamfer(TransitionFeature):
    class Meta:
        name = "chamfer"

    angle_to_plane: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    first_offset_amount: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ClassifiedElementSelect:
    class Meta:
        name = "classified_element_select"

    item_version: Optional[ItemVersion] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item: Optional[Item] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item_definition: Optional[ItemDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document: Optional[Document] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    property: Optional[Property] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    property_value_association: Optional[PropertyValueAssociation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item_instance: Optional[ItemInstance] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document_file: Optional[DocumentFile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document_version: Optional[DocumentVersion] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document_representation: Optional[DocumentRepresentation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    material_designation: Optional[MaterialDesignation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class CompoundFeatureSelect:
    class Meta:
        name = "compound_feature_select"

    machining_feature: Optional[MachiningFeature] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    transition_feature: Optional[TransitionFeature] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class DefinedThread(Thread):
    class Meta:
        name = "defined_thread"

    pitch_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    minor_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    crest: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class DiagonalKnurl(Knurl):
    class Meta:
        name = "diagonal_knurl"

    helix_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class DiamondKnurl(Knurl):
    class Meta:
        name = "diamond_knurl"

    helix1_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    helix2_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class EdgeRound(TransitionFeature):
    class Meta:
        name = "edge_round"

    radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    first_offset_amount: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    second_offset_amount: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class EffectiveElementSelect:
    class Meta:
        name = "effective_element_select"

    document: Optional[Document] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    classification_system: Optional[ClassificationSystem] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document_file: Optional[DocumentFile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document_representation: Optional[DocumentRepresentation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document_version: Optional[DocumentVersion] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item: Optional[Item] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item_version: Optional[ItemVersion] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item_instance: Optional[ItemInstance] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    property: Optional[Property] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    property_value_association: Optional[PropertyValueAssociation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    material_designation: Optional[MaterialDesignation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item_structure_association: Optional[ItemStructureAssociation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    realized_item_association: Optional[RealizedItemAssociation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    physical_item_state_association: Optional[PhysicalItemStateAssociation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    physical_item_location_association: Optional[PhysicalItemLocationAssociation] = (
        field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://digital-thread.re/dt_asset",
            },
        )
    )
    physical_item_structure_association: Optional[PhysicalItemStructureAssociation] = (
        field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://digital-thread.re/dt_asset",
            },
        )
    )


@dataclass
class GeneralOutsideProfile(ProfileFeature):
    class Meta:
        name = "general_outside_profile"

    feature_boundary: Optional[Profile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class GeneralRevolution(RevolvedFeature):
    class Meta:
        name = "general_revolution"

    outer_edge_profile: Optional[GeneralProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class Groove(RevolvedFeature):
    class Meta:
        name = "groove"

    sweep: Optional[OpenProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class OuterDiameter(OuterRound):
    class Meta:
        name = "outer_diameter"

    diameter_at_placement: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    feature_length: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    reduced_size: Optional[TaperSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class OuterDiameterToShoulder(OuterRound):
    class Meta:
        name = "outer_diameter_to_shoulder"

    diameter_at_placement: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    v_shape_boundary: Optional[VeeProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class PlanarFace(MachiningFeature):
    class Meta:
        name = "planar_face"

    course_of_travel: Optional[LinearPath] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    removal_boundary: Optional[LinearProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    face_boundary: Optional[ClosedProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_boss: list[Boss] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class PlaneFinishMilling(PlaneMilling):
    class Meta:
        name = "plane_finish_milling"


@dataclass
class PlaneRoughMilling(PlaneMilling):
    class Meta:
        name = "plane_rough_milling"


@dataclass
class Pocket(MachiningFeature):
    class Meta:
        name = "pocket"

    its_boss: list[Boss] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    slope: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    bottom_condition: Optional[PocketBottomCondition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    planar_radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    orthogonal_radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class RevolvedFlat(RevolvedFeature):
    class Meta:
        name = "revolved_flat"

    flat_edge_shape: Optional[LinearProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class RevolvedRound(RevolvedFeature):
    class Meta:
        name = "revolved_round"

    rounded_edge_shape: Optional[PartialCircularProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ShapeProfile(ProfileFeature):
    class Meta:
        name = "shape_profile"

    floor_condition: Optional[ProfileSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    removal_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class SideFinishMilling(SideMilling):
    class Meta:
        name = "side_finish_milling"


@dataclass
class SideRoughMilling(SideMilling):
    class Meta:
        name = "side_rough_milling"


@dataclass
class Step(MachiningFeature):
    class Meta:
        name = "step"

    open_boundary: Optional[LinearPath] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    wall_boundary: Optional[VeeProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    its_boss: list[Boss] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class StraightKnurl(Knurl):
    class Meta:
        name = "straight_knurl"


@dataclass
class SurfaceTextureParameter:
    class Meta:
        name = "surface_texture_parameter"

    its_value: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    parameter_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    measuring_method: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    parameter_index: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    applied_surfaces: list[MachinedSurface] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ToolKnurl(Knurl):
    class Meta:
        name = "tool_knurl"


@dataclass
class CircularClosedShapeProfile(ShapeProfile):
    class Meta:
        name = "circular_closed_shape_profile"

    closed_boundary: Optional[CircularClosedProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ClassificationAssociation:
    class Meta:
        name = "classification_association"

    associated_classification: Optional[GeneralClassification] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    classified_element: Optional[ClassifiedElementSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    defintional: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    role: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class ClosedPocket(Pocket):
    class Meta:
        name = "closed_pocket"

    feature_boundary: Optional[ClosedProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class CompoundFeature(Two5DManufacturingFeature):
    class Meta:
        name = "compound_feature"

    elements: list[CompoundFeatureSelect] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class EffectivityAssignment:
    class Meta:
        name = "effectivity_assignment"

    assigned_effectivity: Optional[Effectivity] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    effective_element: Optional[EffectiveElementSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    effectivity_indication: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    role: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class GeneralShapeProfile(ShapeProfile):
    class Meta:
        name = "general_shape_profile"

    profile_boundary: Optional[Profile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class OpenPocket(Pocket):
    class Meta:
        name = "open_pocket"

    open_boundary: Optional[OpenProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    wall_boundary: Optional[OpenProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )


@dataclass
class PartialCircularShapeProfile(ShapeProfile):
    class Meta:
        name = "partial_circular_shape_profile"

    open_boundary: Optional[PartialCircularProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class RectangularClosedShapeProfile(ShapeProfile):
    class Meta:
        name = "rectangular_closed_shape_profile"

    closed_boundary: Optional[RectangularClosedProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class RectangularOpenShapeProfile(ShapeProfile):
    class Meta:
        name = "rectangular_open_shape_profile"

    open_boundary: Optional[SquareUProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class ClassificationAssociationRelationship:
    class Meta:
        name = "classification_association_relationship"

    related: Optional[ClassificationAssociation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relating: Optional[ClassificationAssociation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    relationship_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class CounterboreHole(CompoundFeature):
    class Meta:
        name = "counterbore_hole"


@dataclass
class CountersunkHole(CompoundFeature):
    class Meta:
        name = "countersunk_hole"


@dataclass
class GeneralOrganizationalDataSelect:
    class Meta:
        name = "general_organizational_data_select"

    classification_association: Optional[ClassificationAssociation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    classification_system: Optional[ClassificationSystem] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item_definition: Optional[ItemDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document: Optional[Document] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document_file: Optional[DocumentFile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document_representation: Optional[DocumentRepresentation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    document_version: Optional[DocumentVersion] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    general_classification: Optional[GeneralClassification] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item: Optional[Item] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item_structure_association: Optional[ItemStructureAssociation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item_instance: Optional[ItemInstance] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item_version: Optional[ItemVersion] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    item_version_relationship: Optional[ItemVersionRelationship] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    person_in_organization: Optional[PersonInOrganization] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    property: Optional[Property] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    property_value_association: Optional[PropertyValueAssociation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    material_designation: Optional[MaterialDesignation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    physical_item_structure_association: Optional[PhysicalItemStructureAssociation] = (
        field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://digital-thread.re/dt_asset",
            },
        )
    )


@dataclass
class PersonOrganizationAssignment:
    class Meta:
        name = "person_organization_assignment"

    assigned_person_organization: Optional[PersonOrganizationSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )
    description: Optional[StringSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    is_applied_to: list[GeneralOrganizationalDataSelect] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
        },
    )
    role: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "required": True,
        },
    )


@dataclass
class DtCuttingTool13399(DtCuttingTool):
    class Meta:
        name = "dt_cutting_tool_13399"

    alias_identification: list[AliasIdentification] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    application_context: list[ApplicationContext13399] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    assembly_association: list[AssemblyAssociation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    assembly_definition: list[AssemblyDefinition] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    cartesian_coordinate_space: list[CartesianCoordinateSpace] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    cartesian_coordinate_space_2d: list[CartesianCoordinateSpace2D] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    cartesian_coordinate_space_3d: list[CartesianCoordinateSpace3D] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    cartesian_point: list[CartesianPoint] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    classification_association: list[ClassificationAssociation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    classification_association_relationship: list[
        ClassificationAssociationRelationship
    ] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    classification_attribute: list[ClassificationAttribute] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    classification_system: list[ClassificationSystem] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    coating: list[Coating] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    coupling: list[Coupling] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    cutting_condition: list[CuttingCondition] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    cutting_data_association: list[CuttingDataAssociation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    date_time: list[DateTime] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    default_language_string: list[DefaultLanguageString] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    digital_document: list[DigitalDocument] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    digital_file: list[DigitalFile] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    din4000_reference: list[Din4000Reference] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    direction: list[Direction] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    document: list[Document] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    document_assignment: list[DocumentAssignment] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    document_content_property: list[DocumentContentProperty] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    document_creation_property: list[DocumentCreationProperty] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    document_file: list[DocumentFile] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    document_format_property: list[DocumentFormatProperty] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    document_location_property: list[DocumentLocationProperty] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    document_representation: list[DocumentRepresentation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    document_size_property: list[DocumentSizeProperty] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    document_type_property: list[DocumentTypeProperty] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    document_version: list[DocumentVersion] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    document_version_relationship: list[DocumentVersionRelationship] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    duration: list[Duration] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    effectivity: list[Effectivity] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    effectivity_assignment: list[EffectivityAssignment] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    effectivity_relationship: list[EffectivityRelationship] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    external_file_id_and_location: list[ExternalFileIdAndLocation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    external_geometric_model: list[ExternalGeometricModel] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    external_library_reference: list[ExternalLibraryReference] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    external_model: list[ExternalModel] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    external_picture: list[ExternalPicture] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    general_classification: list[GeneralClassification] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    general_classification_hierarchy: list[GeneralClassificationHierarchy] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    geometric_model_relationship_with_transformation: list[
        GeometricModelRelationshipWithTransformation
    ] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    grade: list[Grade] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    grade_relationship: list[GradeRelationship] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    item: list[Item] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    item_characteristic_association: list[ItemCharacteristicAssociation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    item_definition: list[ItemDefinition] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    item_definition_relationship: list[ItemDefinitionRelationship] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    item_instance: list[ItemInstance] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    item_structure_association: list[ItemStructureAssociation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    item_version: list[ItemVersion] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    item_version_relationship: list[ItemVersionRelationship] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    language: list[Language] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    limits_and_fits: list[LimitsAndFits] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    location: list[Location] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    mated_item_relationship: list[MatedItemRelationship] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    material_designation: list[MaterialDesignation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    mating_association: list[MatingAssociation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    mating_definition: list[MatingDefinition] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    multi_language_string: list[MultiLanguageString] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    named_size: list[NamedSize] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    numerical_value: list[NumericalValue] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    organization: list[Organization] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    person: list[Person] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    person_in_organization: list[PersonInOrganization] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    person_organization_assignment: list[PersonOrganizationAssignment] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    physical_document: list[PhysicalDocument] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    physical_file: list[PhysicalFile] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    physical_item: list[PhysicalItem] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    physical_item_definition: list[PhysicalItemDefinition] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    physical_item_location_association: list[PhysicalItemLocationAssociation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    physical_item_state_association: list[PhysicalItemStateAssociation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    physical_item_structure_association: list[PhysicalItemStructureAssociation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    physical_item_version: list[PhysicalItemVersion] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    plib_class_reference: list[PlibClassReference] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    plib_property_reference: list[PlibPropertyReference] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    plus_minus_bounds: list[PlusMinusBounds] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    property: list[Property] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    property_relationship: list[PropertyRelationship] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    property_value: list[PropertyValue] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    property_value_association: list[PropertyValueAssociation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    property_value_representation: list[PropertyValueRepresentation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    property_value_representation_relationship: list[
        PropertyValueRepresentationRelationship
    ] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    quantified_instance: list[QuantifiedInstance] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    realized_item_association: list[RealizedItemAssociation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    rectangular_size: list[RectangularSize] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    specific_item_classification: list[SpecificItemClassification] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    specific_item_classification_hierarchy: list[
        SpecificItemClassificationHierarchy
    ] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    state: list[State] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    string_value: list[StringValue] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    string_with_language: list[StringWithLanguage] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    substrate: list[Substrate] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    transformation: list[Transformation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    transformation_2d: list[Transformation2D] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    transformation_3d: list[Transformation3D] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    unit: list[Unit] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    value_limit: list[ValueLimit] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    value_limitation: list[ValueLimitation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    value_list: list[ValueList] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    value_range: list[ValueRange] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    value_with_unit: list[ValueWithUnit] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )
    workpiece_feature: list[WorkpieceFeature] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/dt_asset",
            "min_occurs": 1,
        },
    )


@dataclass
class DtAsset:
    class Meta:
        name = "dt_asset"
        namespace = "http://digital-thread.re/dt_asset"

    asset_global_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    asset_kind: Optional[DtAssetKind] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    # DtElement를 상속하는 모든 자식 클래스들을 Union으로 묶고, choices 메타데이터를 추가.
    dt_elements: List[object] = field(
        default_factory=list,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "dt_elements",
                    "type": DtProject,
                    "namespace": "http://digital-thread.re/dt_asset",
                },
                {
                    "name": "dt_elements",
                    "type": DtCuttingTool,
                    "namespace": "http://digital-thread.re/dt_asset",
                },
                {
                    "name": "dt_elements",
                    "type": DtMaterial,
                    "namespace": "http://digital-thread.re/dt_asset",
                },
                {
                    "name": "dt_elements",
                    "type": DtFile,
                    "namespace": "http://digital-thread.re/dt_asset",
                },
                # DtElement를 상속하는 다른 모든 타입을 여기에 추가 필요.
            ),
        },
    )

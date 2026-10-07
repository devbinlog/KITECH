from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

__NAMESPACE__ = "http://digital-thread.re/iso14649"


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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    street_number: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    street: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    postal_box: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    town: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    region: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    postal_code: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    country: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    facsimile_number: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    telephone_number: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    electronic_mail_address: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    telex_number: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


class AheadOrBehind(Enum):
    AHEAD = "ahead"
    EXACT = "exact"
    BEHIND = "behind"


@dataclass
class AngleTaper:
    class Meta:
        name = "angle_taper"

    angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    corner_chamfer_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    corner_chamfer_width: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    index: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    max_speed: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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


class CutmodeType(Enum):
    CLIMB = "climb"
    CONVENTIONAL = "conventional"


@dataclass
class Date:
    class Meta:
        name = "date"

    year_component: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    reduced_feed_at_start: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    depth_of_start: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    reduced_cut_at_end: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    reduced_feed_at_end: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    depth_of_end: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    dwell_revolution: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    feed_per_rev_type: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


class FittingType(Enum):
    SHAFT = "shaft"
    HOLE = "hole"


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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class Label:
    class Meta:
        name = "label"

    label: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class MachineFunctions:
    class Meta:
        name = "machine_functions"


@dataclass
class MachiningTool:
    class Meta:
        name = "machining_tool"

    its_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_value: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    initial_value: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class ParameterValue:
    class Meta:
        name = "parameter_value"

    parameter_value: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    last_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    first_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    middle_names: List[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    prefix_titles: List[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    suffix_titles: List[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    lower_limit: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    significant_digits: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class ProcessModel:
    class Meta:
        name = "process_model"

    ini_data_file: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    column_index: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    context_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


class RotDirection(Enum):
    CW = "cw"
    CCW = "ccw"


@dataclass
class RotSpeedMeasure:
    class Meta:
        name = "rot_speed_measure"

    rot_speed_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class SetupInstruction:
    class Meta:
        name = "setup_instruction"

    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    external_document: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    class_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


class SpeedName(Enum):
    RAPID = "RAPID"


class StrokeConnectionStrategy(Enum):
    STRAGHTLINE = "straghtline"
    LIFT_SHIFT_PLUNGE = "lift_shift_plunge"
    DEGOUGE = "degouge"
    LOOP_BACK = "loop_back"


@dataclass
class Text:
    class Meta:
        name = "text"

    text: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    scallop_height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class ToolDirection:
    class Meta:
        name = "tool_direction"


class ToolReferencePoint(Enum):
    TCP = "tcp"
    CCP = "ccp"


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
class TouchProbe:
    class Meta:
        name = "touch_probe"

    its_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class TouchProbing:
    class Meta:
        name = "touch_probing"


@dataclass
class TurningMachiningStrategy:
    class Meta:
        name = "turning_machining_strategy"

    overcut_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    allow_multiple_passes: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    cutting_depth: List[float] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    variable_feedrate: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    allow_multiple_passes: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_milling_tolerances: Optional[Tolerances] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    level: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    operand2: Optional[BooleanExpression] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    month_component: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class CenterMilling(Two5DMillingStrategy):
    class Meta:
        name = "center_milling"


@dataclass
class ContourParallel(Two5DMillingStrategy):
    class Meta:
        name = "contour_parallel"

    rotation_direction: Optional[RotDirection] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    cutmode: Optional[CutmodeType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    cutmode: Optional[CutmodeType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    minute_offset: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    sense: Optional[AheadOrBehind] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
class FreeformStrategy:
    class Meta:
        name = "freeform_strategy"

    pathmode: Optional[PathmodeType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    cutmode: Optional[CutmodeType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_milling_tolerances: Optional[Tolerances] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    stepover: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


@dataclass
class PowerMillingFreeformStrategy(FreeformStrategy):
    class Meta:
        name = "powermilling_freeform_strategy"

    cutmode1: Optional[CutmodeType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    cutmode2: Optional[CutmodeType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class GeometricRepresentationItem(RepresentationItem):
    class Meta:
        name = "geometric_representation_item"


@dataclass
class LimitsAndFits:
    class Meta:
        name = "limits_and_fits"

    deviation: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    grade: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_fitting_type: Optional[FittingType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


@dataclass
class LoopSlotEndType(SlotEndType):
    class Meta:
        name = "loop_slot_end_type"


@dataclass
class Material:
    class Meta:
        name = "material"

    standard_identifier: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    material_identifier: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    material_property: List[PropertyParameter] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


@dataclass
class MultipleArityBooleanExpression(BooleanExpression):
    class Meta:
        name = "multiple_arity_boolean_expression"

    operands: List[BooleanExpression] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 2,
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_parameter_unit: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class OffsetVector:
    class Meta:
        name = "offset_vector"

    translate: List[NcVariable] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 3,
            "max_occurs": 3,
        },
    )
    rotate: List[NcVariable] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_address: Optional[Address] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


@dataclass
class PlanarPocketBottomCondition(PocketBottomCondition):
    class Meta:
        name = "planar_pocket_bottom_condition"


@dataclass
class ProcessModelList:
    class Meta:
        name = "process_model_list"

    its_list: List[ProcessModel] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 1,
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
class Representation:
    class Meta:
        name = "representation"

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    items: List[RepresentationItem] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 1,
        },
    )
    context_of_items: Optional[RepresentationContext] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    nc_variable: Optional[NcVariable] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


@dataclass
class Specification:
    class Meta:
        name = "specification"

    constraint: List[SpecificationUsageConstraint] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    specification_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    specification_description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    specification_class: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    const_cutting_speed: Optional[ConstCuttingSpeed] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    feedrate_reference: Optional[ToolReferencePoint] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    threading_direction: Optional[ThreadingDirectionType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    path_return_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    lift_height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
class TopologicalRepresentationItem(RepresentationItem):
    class Meta:
        name = "topological_representation_item"


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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_rvalue: Optional[Rvalue] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class ComparisonExpression(BooleanExpression):
    class Meta:
        name = "comparison_expression"

    operand1: Optional[NcVariable] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    operand2: Optional[Rvalue] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_material: Optional[Material] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    expected_tool_life: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_technology: Optional[Technology] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


@dataclass
class DefinitionalRepresentation(Representation):
    class Meta:
        name = "definitional_representation"


@dataclass
class Direction(GeometricRepresentationItem):
    class Meta:
        name = "direction"

    direction_ratios: List[float] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 2,
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    yaw_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
class IfStatement(ProgramStructure):
    class Meta:
        name = "if_statement"

    condition: Optional[BooleanExpression] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    true_branch: Optional[Executable] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    false_branch: Optional[Executable] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    minute_component: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    second_component: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    zone: Optional[CoordinatedUniversalTimeOffset] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class Loop(TopologicalRepresentationItem):
    class Meta:
        name = "loop"


@dataclass
class MillingTechnology(Technology):
    class Meta:
        name = "milling_technology"

    cutspeed: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    spindle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    feedrate_per_tooth: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    synchronize_spindle_with_feed: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    inhibit_feedrate_override: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    inhibit_spindle_override: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_adaptive_control: Optional[AdaptiveControl] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


@dataclass
class NonSequential(ProgramStructure):
    class Meta:
        name = "non_sequential"

    its_elements: List[Executable] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 2,
        },
    )


@dataclass
class NotExpression(UnaryBooleanExpression):
    class Meta:
        name = "not_expression"


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

    branches: List[Executable] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 2,
        },
    )


@dataclass
class Point(GeometricRepresentationItem):
    class Meta:
        name = "point"


@dataclass
class ProfileFloor:
    class Meta:
        name = "profile_floor"

    floor_radius: Optional[NumericParameter] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    start_or_end: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class ProgramStop(NcFunction):
    class Meta:
        name = "program_stop"


@dataclass
class Selective(ProgramStructure):
    class Meta:
        name = "selective"

    its_elements: List[Executable] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 2,
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    limits_and_fits: Optional[LimitsAndFits] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    feed_per_revolution: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    sync_spindle_and_z_feed: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    inhibit_feedrate_override: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    inhibit_spindle_override: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_adaptive_control: Optional[AdaptiveControl] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    body: Optional[Executable] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    stepover_direction: Optional[LeftOrRight] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_stroke_connection_strategy: Optional[StrokeConnectionStrategy] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    stepover_direction: Optional[LeftOrRight] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    rotation_direction: Optional[RotDirection] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    spiral_cutmode: Optional[CutmodeType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    stepover_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    stepover_feed: Optional[FeedSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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

    coordinates: List[float] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 1,
            "max_occurs": 3,
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
class ContourBidirectional(Two5DMillingStrategy):
    class Meta:
        name = "contour_bidirectional"

    feed_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    stepover_direction: Optional[LeftOrRight] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    rotation_direction: Optional[RotDirection] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    spiral_cutmode: Optional[CutmodeType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    back_path_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    lift_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    stepover_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    lift_height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    lift_feed: Optional[FeedSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    stepover_feed: Optional[FeedSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    variable_stepover_feed: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    time_component: Optional[LocalTime] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    orientation: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    travel_distance: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


@dataclass
class MillingMachineCuttingTool(MachiningTool):
    class Meta:
        name = "milling_machine_cutting_tool"

    its_cutting_edges: List[CuttingComponent] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 1,
        },
    )
    overall_assembly_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    effective_cutting_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    maximum_depth_of_cut: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    hand_of_cut: Optional[HandOfCutType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    coolant_through_tool: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    coolant_pressure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    mist: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    through_spindle_coolant: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    through_pressure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    axis_clamping: List[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    chip_removal: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    oriented_spindle_stop: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_process_model: Optional[ProcessModelList] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    other_functions: List[PropertyParameter] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    reference_to_curve: Optional[DefinitionalRepresentation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    profile_floor: Optional[ProfileFloor] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    offset_distance: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    row_index: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    column_index: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    implicit_tolerance: Optional[ToleranceSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    coolant_type: Optional[CoolantSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    coolant_pressure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    axis_clamping: List[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    chip_removal: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    oriented_spindle_stop: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_process_model: Optional[ProcessModelList] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    other_functions: List[PropertyParameter] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    tail_stock: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    steady_rest: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    follow_rest: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    cutmode: Optional[CutmodeType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    back_path_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    lift_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    stepover_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    lift_height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    lift_feed: Optional[FeedSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    stepover_feed: Optional[FeedSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    sideward_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class AirStrategy(ApproachRetractStrategy):
    class Meta:
        name = "air_strategy"


@dataclass
class BSplineCurve(BoundedCurve):
    class Meta:
        name = "b_spline_curve"

    degree: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    control_points_list: List[CartesianPoint] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 2,
        },
    )
    curve_form: Optional[BSplineCurveForm] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    closed_curve: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    self_intersect: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    tip_radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    surface_normal: Optional[BoundedCurve] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class Face(TopologicalRepresentationItem):
    class Meta:
        name = "face"

    bounds: List[FaceBound] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 1,
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    corner_radius2: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    to_be: Optional[AdvancedBrepShapeRepresentation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    removal: Optional[AdvancedBrepShapeRepresentation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    edge_radius: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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

    points: List[CartesianPoint] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 2,
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    floor_radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    thread_size: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    thread_pitch: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    taper_thread_count: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class ToolProbing(TouchProbing):
    class Meta:
        name = "tool_probing"

    offset: Optional[CartesianPoint] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    max_wear: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_tool: Optional[MachiningTool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    travel_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    ref_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


@dataclass
class ConnectedFaceSet(TopologicalRepresentationItem):
    class Meta:
        name = "connected_face_set"

    cfs_faces: List[Face] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 1,
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    curve_with_normal_vector: Optional[CurveWithNormalVector] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class PlungeHelix(PlungeStrategy):
    class Meta:
        name = "plunge_helix"

    radius: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    width: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    angle_taper: Optional[AngleTaper] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class TwistDrill(DrillingCuttingTool):
    class Meta:
        name = "twist_drill"


@dataclass
class Block(GeometricRepresentationItem):
    class Meta:
        name = "block"

    position: Optional[Axis2Placement3D] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    x: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    y: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    z: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    placement: Optional[Axis2Placement3D] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    maximum_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    radius: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    positive_ratio_measure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    speed_name: Optional[SpeedName] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


@dataclass
class BoundingGeometrySelect:
    class Meta:
        name = "bounding_geometry_select"

    block: Optional[Block] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    right_circular_cylinder: Optional[RightCircularCylinder] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    advanced_brep_shape_representation: Optional[AdvancedBrepShapeRepresentation] = (
        field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://digital-thread.re/iso14649",
            },
        )
    )


@dataclass
class CircularPath(TravelPath):
    class Meta:
        name = "circular_path"

    radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class ClosedProfile(Profile):
    class Meta:
        name = "closed_profile"


@dataclass
class GeneralPath(TravelPath):
    class Meta:
        name = "general_path"

    swept_path: Optional[BoundedCurve] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class OpenProfile(Profile):
    class Meta:
        name = "open_profile"


@dataclass
class Plane(ElementarySurface):
    class Meta:
        name = "plane"


@dataclass
class Toolpath:
    class Meta:
        name = "toolpath"

    its_priority: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_type: Optional[ToolpathType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_speed: Optional[ToolpathSpeedprofile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_technology: Optional[Technology] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_machine_functions: Optional[MachineFunctions] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class CompleteCircularPath(CircularPath):
    class Meta:
        name = "complete_circular_path"


@dataclass
class Feedstop(Toolpath):
    class Meta:
        name = "feedstop"

    dwell: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    number_of_sides: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    circumscribed_or_across_flats: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    sweep_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    profile_length: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    bounding_geometry_select: Optional[BoundingGeometrySelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    first_radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    first_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    second_radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    second_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    second_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    cross_bar_width: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    cross_bar_depth: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    width: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    first_offset: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    second_offset: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class ToolpathList:
    class Meta:
        name = "toolpath_list"

    its_list: List[Toolpath] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 1,
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    profile_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    tilt_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_material: Optional[Material] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    global_tolerance: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_rawpiece: Optional["Workpiece"] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_geometry: Optional[AdvancedBrepShapeRepresentation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_bounding_geometry: Optional[BoundingGeometrySelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    clamping_positions: List[CartesianPoint] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_tool_direction: Optional[ToolDirection] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    fix_point_dir: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


@dataclass
class AxisTrajectory(Trajectory):
    class Meta:
        name = "axis_trajectory"

    axis_list: List[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 1,
        },
    )
    commands: List[BoundedCurve] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 1,
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    rounded_corner: Optional[RoundedCorner] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    profiled_corner: Optional[ProfiledCorner] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_toolaxis: Optional[BoundedCurve] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_contact_type: Optional[ContactType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_toolaxis: Optional[BoundedCurve] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    surface_normal: Optional[BoundedCurve] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    probing_distance: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_probe: Optional[TouchProbe] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    computed_offset: Optional[OffsetVector] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_workpiece: Optional[Workpiece] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    expected_value: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_probe: Optional[TouchProbe] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_origin: Optional[Axis2Placement3D] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_offset: Optional[OffsetVector] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_restricted_area: Optional[RestrictedAreaSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_instructions: List[SetupInstruction] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    benddist: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    down_dir: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    transition: Optional[CornerTransitionSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    erretract_plane: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    start_point: Optional[CartesianPoint] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_tool: Optional[MachiningTool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_technology: Optional[Technology] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_machine_functions: Optional[MachineFunctions] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class Setup:
    class Meta:
        name = "setup"

    its_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_origin: Optional[Axis2Placement3D] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_secplane: Optional[ElementarySurface] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_workpiece_setup: List[WorkpieceSetup] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


@dataclass
class CuttingEdgeProperties:
    class Meta:
        name = "cutting_edge_properties"

    expected_tool_life: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_technology: Optional[Technology] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    cutting_edge_length: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    tool_cutting_edge_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    tool_cutting_edge_angle_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    tool_included_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    corner_transitions: List[CornerTransition] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    maximum_side_cutting_depth: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    maximum_end_cutting_depth: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_workpiece: Optional[Workpiece] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_operations: List[MachiningOperation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    retract: Optional[ApproachRetractStrategy] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_machining_strategy: Optional[TurningMachiningStrategy] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


@dataclass
class Tdms:
    raw: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    ext: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


@dataclass
class NcCode:
    its_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


@dataclass
class Vm:
    its_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


@dataclass
class Workplan(ProgramStructure):
    class Meta:
        name = "workplan"

    its_elements: List[Executable] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_channel: Optional[Channel] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_setup: Optional[Setup] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_effect: Optional[InProcessGeometry] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    tdms: List[Tdms] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    nc_code: List[NcCode] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    vm: List[Vm] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    previous_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    dwell_time_bottom: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    feed_on_retract: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_machining_strategy: Optional[DrillingTypeStrategy] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    allowance: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


@dataclass
class Knurling(TurningMachiningOperation):
    class Meta:
        name = "knurling"


@dataclass
class MachiningWorkingstep(Workingstep):
    class Meta:
        name = "machining_workingstep"

    its_feature: Optional[ManufacturingFeature] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_operation: Optional[MachiningOperation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_effect: Optional[InProcessGeometry] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    retract: Optional[ApproachRetractStrategy] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


@dataclass
class Project:
    class Meta:
        name = "project"
        namespace = "http://digital-thread.re/iso14649"

    its_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    main_workplan: Optional[Workplan] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    its_workpieces: List[Workpiece] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    its_owner: Optional[PersonAndAddress] = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    its_release: Optional[DateAndTime] = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    its_status: Optional[Approval] = field(
        default=None,
        metadata={
            "type": "Element",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    f_dimension: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    minimum_cutting_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    a_dimension_on_f: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    a_dimension_on_lf: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    cutting_edge: Optional[CuttingEdgeProperties] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    hand_of_tool: Optional[HandOfToolType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


@dataclass
class TurningWorkingstep(Workingstep):
    class Meta:
        name = "turning_workingstep"

    its_features: List[ManufacturingFeature] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 2,
        },
    )
    its_operation: Optional[TurningMachiningOperation] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_effect: Optional[InProcessGeometry] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    depth_of_testcut: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    waiting_position: Optional[CartesianPoint] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    maximum_grooving_depth: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    corner_radius: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    maximum_axial_grooving_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    minimum_axial_grooving_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


@dataclass
class MachiningFeature(Two5DManufacturingFeature):
    class Meta:
        name = "machining_feature"

    depth: Optional[ElementarySurface] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    proj_dir: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    depth: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class RegionSurfaceList(Region):
    class Meta:
        name = "region_surface_list"

    surface_list: List[BoundedSurface] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 1,
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    thread_hand: Optional[ThreadHandType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_thread_type: Optional[ThreadType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    thread_profile: Optional[ThreadProfileType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    thread_form_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    slope: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    radial_cutting_depth: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    allowance_side: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    allowance_bottom: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    number_of_feature: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    relocated_base_feature: List[CircularOffset] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    missing_base_feature: List[CircularOmit] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    base_feature_diameter: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    base_feature_rotation: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class CounterSinking(DrillingOperation):
    class Meta:
        name = "counter_sinking"


@dataclass
class Drilling(DrillingOperation):
    class Meta:
        name = "drilling"


@dataclass
class GeneralPattern(ReplicateFeature):
    class Meta:
        name = "general_pattern"

    replicate_locations: List[Axis2Placement3D] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 2,
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    partial_profile: Optional[PartialAreaDefinition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    tooth_depth: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    diametral_pitch: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    root_fillet: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    number_of_teeth: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    major_diameter: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    nominal_diameter: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    surface_element: Optional[BottomOrSide] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    first_depth: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    depth_of_step: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    dwell_time_step: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    allowance_bottom: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    its_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    number_of_rows: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    number_of_columns: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    row_spacing: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    row_layout_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    relocated_base_feature: List[RectangularOffset] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    missing_base_feature: List[RectangularOmit] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    radius: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    change_in_diameter: Optional[TaperSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    bottom_condition: Optional[HoleBottomCondition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    partial_circular_boundary: Optional[PartialCircularProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    radial_cutting_depth: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    allowance_side: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    swept_shape: Optional[OpenProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    end_conditions: List[SlotEndType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    radius: Optional[NumericParameter] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    applied_shape: List[MachiningFeature] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 1,
        },
    )
    inner_or_outer_thread: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    qualifier: Optional[DescriptiveParameter] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    fit_class: Optional[DescriptiveParameter] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    form: Optional[DescriptiveParameter] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    major_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    number_of_threads: Optional[NumericParameter] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    thread_hand: Optional[DescriptiveParameter] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    second_feature: Optional[MachiningFeature] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    first_offset_amount: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
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
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    transition_feature: Optional[TransitionFeature] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    minor_diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    crest: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    helix2_angle: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    first_offset_amount: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    second_offset_amount: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )


@dataclass
class GeneralOutsideProfile(ProfileFeature):
    class Meta:
        name = "general_outside_profile"

    feature_boundary: Optional[Profile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    feature_length: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    reduced_size: Optional[TaperSelect] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    v_shape_boundary: Optional[VeeProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    removal_boundary: Optional[LinearProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    face_boundary: Optional[ClosedProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_boss: List[Boss] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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

    its_boss: List[Boss] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    slope: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    bottom_condition: Optional[PocketBottomCondition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    planar_radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    orthogonal_radius: Optional[TolerancedLengthMeasure] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    removal_direction: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    wall_boundary: Optional[VeeProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    its_boss: List[Boss] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    parameter_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    measuring_method: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    parameter_index: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
        },
    )
    applied_surfaces: List[MachinedSurface] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 1,
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )


@dataclass
class CompoundFeature(Two5DManufacturingFeature):
    class Meta:
        name = "compound_feature"

    elements: List[CompoundFeatureSelect] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "min_occurs": 2,
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )
    wall_boundary: Optional[OpenProfile] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
            "namespace": "http://digital-thread.re/iso14649",
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
class PowerMillBottomAndSideMilling(BottomAndSideMilling):
    class Meta:
        name = "powermill_bottom_and_side_milling"

    its_freeform_strategy: Optional[PowerMillingFreeformStrategy] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )

    XAxisVector: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )

    YAxisVector: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )

    ZAxisVector: Optional[Direction] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://digital-thread.re/iso14649",
            "required": True,
        },
    )

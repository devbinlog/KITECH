"""Equipment data parsers package."""

from .base_parser import BaseParser
from .cnc_parser import CncParser
from .robot_parser import RobotParser
from .plc_parser import PlcParser

# Parser registry
_PARSERS = {
    "CNC": CncParser(),
    "ROBOT": RobotParser(),
    "AMR": RobotParser(),  # AMR uses same parser as Robot
    "PLC": PlcParser(),
}


def get_parser(equipment_type: str) -> BaseParser:
    """
    Get parser for equipment type.

    Args:
        equipment_type: Equipment type (CNC, ROBOT, AMR, PLC)

    Returns:
        Parser instance
    """
    return _PARSERS.get(equipment_type.upper(), CncParser())


__all__ = [
    "BaseParser",
    "CncParser",
    "RobotParser",
    "PlcParser",
    "get_parser",
]

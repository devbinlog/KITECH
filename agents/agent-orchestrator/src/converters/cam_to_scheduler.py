"""
CAM Analysis Result → Cell Scheduler Input Converter

Converts CAM runner output to the format expected by cell_scheduler_agent.py
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class CamToSchedulerConverter:
    """
    Converts CAM analysis results to cell-scheduler input format.

    The cell_scheduler_agent expects a specific nested structure:
    - request.scheduling_request.scheduling_horizon.start/end
    - work_orders[].jobs[].operations[].nc_code
    - machines[]
    - machine_type_params
    """

    def __init__(
        self,
        default_setup_time: int = 5,
        default_machine_type: str = "CNC",
        horizon_days: int = 7,
    ):
        """
        Initialize converter.

        Args:
            default_setup_time: Default setup time in minutes
            default_machine_type: Default machine type for operations
            horizon_days: Scheduling horizon in days
        """
        self.default_setup_time = default_setup_time
        self.default_machine_type = default_machine_type
        self.horizon_days = horizon_days

    def convert(
        self,
        cam_data: Dict[str, Any],
        gcode_data: Optional[Dict[str, Any]] = None,
        machines: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Convert CAM analysis result to scheduler input format.

        Args:
            cam_data: CAM analysis result with cutting paths and cycle time
            gcode_data: Optional G-code parsing result for additional context
            machines: Optional machine configuration (defaults to single CNC)

        Returns:
            Dictionary formatted for cell-scheduler agent
        """
        now = datetime.now()
        horizon_start = now.isoformat()
        horizon_end = (now + timedelta(days=self.horizon_days)).isoformat()

        # Extract cycle time from CAM data
        cycle_time_info = self._extract_cycle_time(cam_data)

        # Extract tool info
        tool_info = self._extract_tool_info(cam_data, gcode_data)

        # Create work orders
        work_orders = self._create_work_orders(
            cam_data, gcode_data, cycle_time_info, tool_info, horizon_start
        )

        # Create or use provided machines
        if machines is None:
            machines = self._create_default_machines(horizon_start)

        # Build the complete input structure
        scheduler_input = {
            "request": {
                "scheduling_request": {
                    "scheduling_horizon": {"start": horizon_start, "end": horizon_end},
                    "options": {"solver_type": "OR_TOOLS", "solver_time_limit_sec": 30},
                }
            },
            "work_orders": work_orders,
            "machines": machines,
            "machine_type_params": self._create_machine_type_params(),
        }

        logger.info(
            f"Converted CAM data: {len(work_orders)} work orders, "
            f"{len(machines)} machines, cycle_time={cycle_time_info['total_min']:.1f}min"
        )

        return scheduler_input

    def _extract_cycle_time(self, cam_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract cycle time information from CAM data."""
        cycle_time = cam_data.get("cycle_time", {})
        summary = cam_data.get("summary", {})

        if isinstance(cycle_time, dict):
            # Try both naming conventions
            total_min = cycle_time.get("total_cycle_time_min", cycle_time.get("total_min", 0))
            total_sec = cycle_time.get("total_cycle_time_sec", cycle_time.get("total_sec", 0))
            cutting_min = (
                cycle_time.get("cutting_time_sec", 0) / 60
                if cycle_time.get("cutting_time_sec")
                else cycle_time.get("cutting_min", 0)
            )
            rapid_min = (
                cycle_time.get("rapid_time_sec", 0) / 60
                if cycle_time.get("rapid_time_sec")
                else cycle_time.get("rapid_min", 0)
            )

            # If total_min is still 0 but we have total_sec, convert
            if total_min == 0 and total_sec > 0:
                total_min = total_sec / 60
        else:
            total_min = 0
            cutting_min = 0
            rapid_min = 0

        # Fallback to summary if cycle_time is empty
        if total_min == 0:
            total_min = summary.get("total_cycle_time_min", 10.0)

        # Ensure minimum cycle time
        total_min = max(total_min, 1.0)

        return {
            "total_min": total_min,
            "cutting_min": cutting_min,
            "rapid_min": rapid_min,
            "total_sec": total_min * 60,
        }

    def _extract_tool_info(
        self, cam_data: Dict[str, Any], gcode_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract tool information from CAM and G-code data."""
        summary = cam_data.get("summary", {})

        tool_info = {
            "tool_id": summary.get("tool_id", 1),
            "tool_name": summary.get("tool_name", "Default Tool"),
            "tool_diameter": summary.get("cutter_diameter", 6.0),
            "tool_list": [],
            "tool_change_count": 0,
        }

        # Extract from G-code data if available
        if gcode_data:
            gcode_summary = gcode_data.get("data", {}).get("summary", {})
            tools = gcode_summary.get("tools_used", [])
            if tools:
                tool_info["tool_list"] = [str(t) for t in tools]
                tool_info["tool_change_count"] = len(tools) - 1 if len(tools) > 1 else 0

        return tool_info

    def _create_work_orders(
        self,
        cam_data: Dict[str, Any],
        gcode_data: Optional[Dict[str, Any]],
        cycle_time: Dict[str, float],
        tool_info: Dict[str, Any],
        horizon_start: str,
    ) -> List[Dict[str, Any]]:
        """Create work orders from CAM data."""
        now = datetime.fromisoformat(horizon_start.replace("Z", "+00:00").split("+")[0])

        # Get program ID from gcode_data if available
        program_id = "GCODE-PART"
        file_path = "inline_gcode.nc"
        if gcode_data:
            data = gcode_data.get("data", {})
            program_id = data.get("program_number", program_id)
            file_path = data.get("input_source", file_path)

        # Create NC code definition (OR-Tools requires integer cycle time)
        nc_code = {
            "program_id": program_id,
            "file_path": file_path,
            "cycle_time_sec": int(round(cycle_time["total_sec"])),
            "cycle_time_confidence": 0.9,
            "tool_list": tool_info["tool_list"],
            "tool_change_count": tool_info["tool_change_count"],
            "compatible_machines": [self.default_machine_type],
        }

        # Create operation with all required fields
        operation = {
            "op_id": "OP-001",
            "op_name": "Machining",
            "sequence": 1,
            "predecessors": [],
            "required_machine_type": self.default_machine_type,
            "setup_id": "SETUP-DEFAULT",
            "setup_time": self.default_setup_time,
            "nc_code": nc_code,
        }

        # Create job
        job = {
            "job_id": "JOB-001",
            "job_name": "Main Job",
            "sequence": 1,
            "operations": [operation],
        }

        # Create work order
        work_order = {
            "wo_id": f"WO-CAM-{now.strftime('%H%M%S')}",
            "product_id": program_id,
            "product_name": f"Part from {file_path}",
            "order_quantity": 1,
            "release_date": now.isoformat(),
            "due_date": (now + timedelta(days=1)).isoformat(),
            "priority": 1,
            "customer": "Internal",
            "jobs": [job],
        }

        return [work_order]

    def _create_default_machines(self, available_from: str) -> List[Dict[str, Any]]:
        """Create default machine configuration."""
        return [
            {
                "machine_id": "CNC-001",
                "machine_name": "CNC Machine 1",
                "machine_type": self.default_machine_type,
                "status": "available",
                "available_from": available_from,
                "efficiency": 1.0,
            }
        ]

    def _create_machine_type_params(self) -> Dict[str, Any]:
        """Create machine type parameters."""
        return {
            self.default_machine_type: {
                "setup_time_default": self.default_setup_time,
                "processing_speed_factor": 1.0,
                "efficiency_factor": 0.85,
                "maintenance_buffer_min": 5,
            }
        }


# Convenience function
def convert_cam_to_scheduler(
    cam_data: Dict[str, Any], gcode_data: Optional[Dict[str, Any]] = None, **kwargs
) -> Dict[str, Any]:
    """
    Convert CAM analysis result to scheduler input.

    Args:
        cam_data: CAM analysis result
        gcode_data: Optional G-code parsing result
        **kwargs: Additional options for converter

    Returns:
        Scheduler input dictionary
    """
    converter = CamToSchedulerConverter(**kwargs)
    return converter.convert(cam_data, gcode_data)

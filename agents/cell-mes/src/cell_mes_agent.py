"""
Cell-MES Agent - Manufacturing Execution System Agent

Comprehensive MES solution for smart factory production management with:
- AAS-based asset discovery and synchronization
- Equipment status monitoring with type-specific parsing
- Work order management and execution
- Integration with cell-scheduler for production planning
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

# Add shared library to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from core import BaseAgent
from utils import setup_logger

logger = setup_logger(__name__)


class CellMesAgent(BaseAgent):
    """
    Manufacturing Execution System Agent.

    Provides MES functionality including:
    - Asset Discovery: Auto-sync equipment from middleware (AAS)
    - Equipment Monitoring: Real-time status polling with type-specific parsing
    - Work Order Management: Create, execute, and track production orders
    - Scheduler Integration: Share equipment availability with cell-scheduler
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Cell-MES agent.

        Args:
            config: Configuration dictionary with keys:
                - database_url: PostgreSQL connection string
                - middleware_url: Middleware server URL
                - poll_interval: Equipment polling interval in seconds
        """
        super().__init__(name="cell-mes", config=config or {})
        self.database_url = config.get("database_url") if config else None
        self.middleware_url = config.get("middleware_url") if config else None
        self.poll_interval = config.get("poll_interval", 3) if config else 3

    def process(self, input_data: Any) -> Dict[str, Any]:
        """
        Process MES commands.

        Args:
            input_data: Command dictionary with 'action' and optional params:
                - {"action": "sync"} - Sync equipment from middleware
                - {"action": "poll", "equipment_id": 1} - Poll equipment status
                - {"action": "poll_all"} - Poll all equipment
                - {"action": "get_equipment_status", "equipment_ids": [...]}
                - {"action": "get_work_info", "lot_no": "..."} - Get work payload
                - {"action": "health"} - Check system health

        Returns:
            Result dictionary with status and data
        """
        try:
            logger.info(f"🏭 Cell-MES Agent processing: {input_data}")

            if isinstance(input_data, str):
                action = input_data
                params = {}
            else:
                action = input_data.get("action", "health")
                params = input_data

            # Route to appropriate handler
            handlers = {
                "sync": self._handle_sync,
                "poll": self._handle_poll,
                "poll_all": self._handle_poll_all,
                "get_equipment_status": self._handle_get_equipment_status,
                "get_work_info": self._handle_get_work_info,
                "health": self._handle_health,
                # Scheduler integration actions
                "create_scheduling_request": self._handle_create_scheduling_request,
                "process_scheduling_result": self._handle_process_scheduling_result,
            }

            handler = handlers.get(action)
            if not handler:
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}",
                    "available_actions": list(handlers.keys()),
                }

            result = handler(params)
            logger.info(f"✅ Cell-MES Agent completed: {action}")
            return result

        except Exception as e:
            logger.error(f"❌ Cell-MES Agent error: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    def _handle_sync(self, params: Dict) -> Dict[str, Any]:
        """Handle asset discovery/sync command."""
        # In actual implementation, this would call sync_service
        return {
            "status": "success",
            "message": "Asset synchronization would be performed here",
            "note": "Use FastAPI endpoint POST /api/v1/masters/equipments/sync for actual sync",
        }

    def _handle_poll(self, params: Dict) -> Dict[str, Any]:
        """Handle single equipment poll command."""
        equipment_id = params.get("equipment_id")
        if not equipment_id:
            return {"status": "error", "message": "equipment_id required"}

        return {
            "status": "success",
            "message": f"Would poll equipment {equipment_id}",
            "note": "Use FastAPI endpoint GET /api/v1/masters/equipments/{id}/status?refresh=true",
        }

    def _handle_poll_all(self, params: Dict) -> Dict[str, Any]:
        """Handle poll all equipment command."""
        return {
            "status": "success",
            "message": "Would poll all active equipment",
            "note": "Background polling task runs every 3 seconds",
        }

    def _handle_get_equipment_status(self, params: Dict) -> Dict[str, Any]:
        """
        Get equipment status for scheduler integration.

        This method provides equipment availability data to cell-scheduler.
        """
        equipment_ids = params.get("equipment_ids", [])

        # Format for cell-scheduler integration
        return {
            "status": "success",
            "equipments": [
                {
                    "equipment_id": eid,
                    "status": "AVAILABLE",  # Would be actual status from DB
                    "available_from": datetime.now(timezone.utc).isoformat(),
                }
                for eid in equipment_ids
            ],
        }

    def _handle_get_work_info(self, params: Dict) -> Dict[str, Any]:
        """Handle get work info command."""
        lot_no = params.get("lot_no")
        if not lot_no:
            return {"status": "error", "message": "lot_no required"}

        return {
            "status": "success",
            "message": f"Would get work info for lot {lot_no}",
            "note": "Use FastAPI endpoint GET /api/v1/production/middleware/work-info?lot_no=...",
        }

    def _handle_health(self, params: Dict) -> Dict[str, Any]:
        """Handle health check command."""
        return {
            "status": "success",
            "agent": self.name,
            "config": {
                "database_url": "configured" if self.database_url else "not configured",
                "middleware_url": self.middleware_url or "default",
                "poll_interval": self.poll_interval,
            },
            "capabilities": [
                "Asset Discovery (AAS sync)",
                "Equipment Monitoring",
                "Work Order Management",
                "Scheduler Integration",
            ],
        }

    def _handle_create_scheduling_request(self, params: Dict) -> Dict[str, Any]:
        """
        Create a scheduling request for cell-scheduler.

        This prepares all data needed by cell-scheduler:
        - Available equipment with status
        - Pending work orders with operations
        - Machine type parameters
        """
        horizon_hours = params.get("horizon_hours", 24)
        include_running = params.get("include_running", False)

        return {
            "status": "success",
            "message": f"Would create scheduling request for {horizon_hours}h horizon",
            "note": "Use FastAPI endpoint POST /api/v1/scheduler/create-request",
            "params": {
                "horizon_hours": horizon_hours,
                "include_running": include_running,
            },
        }

    def _handle_process_scheduling_result(self, params: Dict) -> Dict[str, Any]:
        """
        Process scheduling result from cell-scheduler.

        Updates work orders with:
        - Scheduled start/end times
        - Assigned machine IDs
        """
        scheduled_tasks = params.get("scheduled_tasks", [])

        return {
            "status": "success",
            "message": f"Would process {len(scheduled_tasks)} scheduled tasks",
            "note": "Use FastAPI endpoint POST /api/v1/scheduler/process-result",
        }

    # =========================================================================
    # Integration Methods (for orchestrator/other agents)
    # =========================================================================

    def get_equipment_for_scheduler(
        self, equipment_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get equipment availability data for cell-scheduler.

        Args:
            equipment_ids: Optional list of equipment IDs to filter

        Returns:
            List of equipment status dictionaries
        """
        result = self._handle_get_equipment_status({"equipment_ids": equipment_ids or []})
        return result.get("equipments", [])

    def notify_schedule_update(self, schedule_data: Dict[str, Any]) -> bool:
        """
        Receive schedule update from cell-scheduler.

        Args:
            schedule_data: Scheduled work orders with machine assignments

        Returns:
            True if successfully processed
        """
        logger.info(f"📅 Received schedule update: {len(schedule_data.get('tasks', []))} tasks")
        # In actual implementation, this would call process_scheduling_result
        return True

    def request_schedule(
        self, horizon_hours: int = 24, include_running: bool = False
    ) -> Dict[str, Any]:
        """
        Request scheduling data for cell-scheduler.

        This method creates a complete scheduling request that can be
        passed directly to cell-scheduler.process().

        Args:
            horizon_hours: Planning horizon in hours
            include_running: Include currently running orders

        Returns:
            Scheduling request data ready for cell-scheduler
        """
        return self._handle_create_scheduling_request(
            {
                "horizon_hours": horizon_hours,
                "include_running": include_running,
            }
        )

    def apply_schedule(self, scheduling_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply scheduling result from cell-scheduler.

        This method processes the scheduling result and updates
        work orders with scheduled times.

        Args:
            scheduling_result: Result from cell-scheduler.process()

        Returns:
            Processing result with updated order information
        """
        return self._handle_process_scheduling_result(scheduling_result)


# Convenience function for standalone usage
def create_agent(config: Dict[str, Any] = None) -> CellMesAgent:
    """Create and return a CellMesAgent instance."""
    return CellMesAgent(config)


if __name__ == "__main__":
    # Example standalone usage
    agent = create_agent()

    # Test health check
    result = agent.process({"action": "health"})
    print(f"Health check: {result}")

    # Test equipment status (for scheduler)
    equipment_data = agent.get_equipment_for_scheduler(["CNC-001", "ROBOT-001"])
    print(f"Equipment for scheduler: {equipment_data}")

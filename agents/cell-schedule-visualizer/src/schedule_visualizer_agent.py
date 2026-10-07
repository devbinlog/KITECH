"""
Manufacturing Schedule Visualizer Agent

Generates schedule data for Next.js frontend visualization:
- Exports schedule data to JSON files
- Runs Flask API server for frontend consumption
- Supports Gantt charts, utilization analysis, and lateness tracking
"""

import json
import sys
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import time

# Add shared library to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from core import BaseAgent
from utils import setup_logger

logger = setup_logger(__name__)


# ============================================================================
# Visualizer
# ============================================================================


class ScheduleVisualizer:
    """Export schedule data for Next.js frontend visualization"""

    def __init__(self, schedule_result: Dict[str, Any]):
        """
        Initialize visualizer with schedule result

        Args:
            schedule_result: Dictionary from CellScheduler.solve()
        """
        self.result = schedule_result
        self.scheduled_tasks = schedule_result.get("scheduled_tasks", [])
        self.quality_metrics = schedule_result.get("quality_metrics", {})
        self.gantt_data = schedule_result.get("gantt_data", {})
        self.statistics = schedule_result.get("statistics", {})

    def export_schedule_json(self, output_path: str) -> bool:
        """
        Export schedule data to JSON file for Next.js frontend

        Args:
            output_path: Path to save JSON file

        Returns:
            True if successful
        """
        logger.info(f"Exporting schedule JSON: {output_path}")

        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Create comprehensive JSON structure for frontend
            export_data = {
                "status": "success",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "schedule": {
                    "scheduled_tasks": self.scheduled_tasks,
                    "quality_metrics": self.quality_metrics,
                    "gantt_data": self.gantt_data,
                    "statistics": self.statistics,
                },
            }

            # Write JSON file
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"✅ Schedule exported: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Error exporting schedule: {e}")
            return False


# ============================================================================
# Agent
# ============================================================================


class ScheduleVisualizerAgent(BaseAgent):
    """
    Manufacturing Schedule Visualization Agent

    Exports schedule data to JSON and provides Flask API server
    for Next.js frontend consumption.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the visualizer agent

        Args:
            config: Configuration dictionary (can include api_port for Flask)
        """
        super().__init__(name="schedule-visualizer", config=config or {})
        self.api_port = (config or {}).get("api_port", 5000)
        self.api_thread: Optional[threading.Thread] = None

    def process(self, input_data: Any) -> Dict[str, Any]:
        """
        Process scheduling result and export to JSON

        Args:
            input_data: Can be either:
                - Path to schedule_result.json
                - Dictionary with schedule result

        Returns:
            Dictionary with JSON path and API status
        """
        try:
            logger.info("🎨 Schedule Visualizer Agent starting...")

            # Load data if path provided
            if isinstance(input_data, str):
                with open(input_data, "r", encoding="utf-8") as f:
                    schedule_result = json.load(f)
            else:
                schedule_result = input_data

            # Create visualizer
            visualizer = ScheduleVisualizer(schedule_result)

            # Export to JSON for frontend
            output_dir = Path(".") / "samples" / "cell-schedule-visualizer" / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            json_path = str(output_dir / "schedule_data.json")

            success = visualizer.export_schedule_json(json_path)

            if success:
                logger.info(f"✅ Schedule data exported: {json_path}")
                return {
                    "status": "success",
                    "json_path": json_path,
                    "message": "Schedule data exported successfully",
                    "format": "json",
                    "data": schedule_result,
                }
            else:
                return {
                    "status": "error",
                    "json_path": json_path,
                    "message": "Failed to export schedule data",
                }

        except Exception as e:
            logger.error(f"❌ Visualization error: {e}", exc_info=True)
            return {"status": "error", "error": str(e), "json_path": None}

    def start_api_server(self, schedule_result: Dict[str, Any], host: str = "127.0.0.1"):
        """
        Start Flask API server in background thread

        Args:
            schedule_result: Schedule result dictionary
            host: Host to bind to
        """
        try:
            # Import here to avoid hard dependency
            from api_server import create_app

            logger.info(f"🚀 Starting API server at http://{host}:{self.api_port}")

            app = create_app(schedule_result)

            # Run in background thread
            def run_server():
                app.run(host=host, port=self.api_port, debug=False, use_reloader=False)

            self.api_thread = threading.Thread(target=run_server, daemon=True)
            self.api_thread.start()

            # Give server time to start
            time.sleep(1)

            logger.info("✅ API server started successfully")
            logger.info("📊 Access frontend at: http://localhost:3000")
            logger.info(f"📡 API endpoints available at: http://{host}:{self.api_port}/api/*")

        except ImportError:
            logger.warning("Flask not available, API server skipped")
        except Exception as e:
            logger.error(f"❌ Failed to start API server: {e}")

    def stop_api_server(self):
        """Stop the API server"""
        if self.api_thread and self.api_thread.is_alive():
            logger.info("Stopping API server...")
            # Flask server will stop when process exits
            pass

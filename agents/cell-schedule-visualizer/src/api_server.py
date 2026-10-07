"""
Flask API Server for Schedule Visualization

Provides REST endpoints for fetching schedule data for the Next.js frontend.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone
from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger

# Add shared library to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from utils import setup_logger

logger = setup_logger(__name__)


def get_cors_origins() -> List[str]:
    """Get CORS origins from environment variable or use defaults."""
    cors_env = os.environ.get("CORS_ORIGINS", "")
    if cors_env:
        return [origin.strip() for origin in cors_env.split(",")]
    # Default development origins
    return [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ]


# ============================================================================
# Flask App Setup
# ============================================================================


def create_app(schedule_result: Dict[str, Any]) -> Flask:
    """
    Create Flask app with schedule data

    Args:
        schedule_result: Schedule result from CellScheduler.solve()

    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    cors_origins = get_cors_origins()
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": cors_origins,
                "methods": ["GET", "POST", "OPTIONS"],
                "allow_headers": ["Content-Type"],
            }
        },
    )

    # Store schedule result in app context
    app.schedule_result = schedule_result

    # Configure Swagger
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs",
    }

    template = {
        "swagger": "2.0",
        "info": {
            "title": "Manufacturing Schedule Visualizer API",
            "description": "API for accessing manufacturing schedule data, metrics, and Gantt chart information.",
            "version": "1.0.0",
        },
    }

    Swagger(app, config=swagger_config, template=template)

    # ========================================================================
    # Routes
    # ========================================================================

    @app.route("/api/health", methods=["GET"])
    def health():
        """Health check endpoint
        ---
        tags:
          - System
        responses:
          200:
            description: System is healthy
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: ok
                timestamp:
                  type: string
        """
        return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})

    @app.route("/api/schedule", methods=["GET"])
    def get_schedule():
        """Get complete schedule data
        ---
        tags:
          - Schedule
        responses:
          200:
            description: Complete schedule data including tasks and metrics
        """
        return jsonify(
            {
                "status": "success",
                "data": app.schedule_result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    @app.route("/api/schedule/gantt", methods=["GET"])
    def get_gantt_data():
        """Get Gantt chart data
        ---
        tags:
          - Visualization
        responses:
          200:
            description: Formatted data for Gantt chart visualization
        """
        gantt_data = app.schedule_result.get("gantt_data", {})
        return jsonify(
            {
                "status": "success",
                "data": gantt_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    @app.route("/api/schedule/metrics", methods=["GET"])
    def get_metrics():
        """Get quality metrics and statistics
        ---
        tags:
          - Analytics
        responses:
          200:
            description: Key performance indicators and schedule statistics
        """
        metrics = app.schedule_result.get("quality_metrics", {})
        statistics = app.schedule_result.get("statistics", {})
        return jsonify(
            {
                "status": "success",
                "metrics": metrics,
                "statistics": statistics,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    @app.route("/api/schedule/tasks", methods=["GET"])
    def get_tasks():
        """Get scheduled tasks"""
        tasks = app.schedule_result.get("scheduled_tasks", [])
        return jsonify(
            {
                "status": "success",
                "tasks": tasks,
                "total": len(tasks),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    @app.route("/api/schedule/utilization", methods=["GET"])
    def get_utilization():
        """Get machine utilization data"""
        metrics = app.schedule_result.get("quality_metrics", {})
        utilization = metrics.get("machine_utilization", {})
        return jsonify(
            {
                "status": "success",
                "data": utilization,
                "average": metrics.get("avg_machine_utilization", 0),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    @app.route("/api/schedule/lateness", methods=["GET"])
    def get_lateness():
        """Get work order lateness data"""
        metrics = app.schedule_result.get("quality_metrics", {})
        lateness = metrics.get("per_wo_lateness", {})
        return jsonify(
            {
                "status": "success",
                "data": lateness,
                "total": metrics.get("total_lateness_hours", 0),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return jsonify({"status": "error", "message": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def server_error(error):
        """Handle 500 errors"""
        logger.error(f"Server error: {error}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

    return app


def run_api_server(
    schedule_result: Dict[str, Any],
    host: str = "127.0.0.1",
    port: int = 5000,
    debug: bool = False,
):
    """
    Run Flask API server

    Args:
        schedule_result: Schedule result from CellScheduler.solve()
        host: Host to bind to
        port: Port to bind to
        debug: Enable debug mode
    """
    app = create_app(schedule_result)
    logger.info(f"🚀 Starting API server at http://{host}:{port}")
    logger.info("📊 Available endpoints:")
    logger.info(f"  GET  http://{host}:{port}/api/health")
    logger.info(f"  GET  http://{host}:{port}/api/schedule")
    logger.info(f"  GET  http://{host}:{port}/api/schedule/gantt")
    logger.info(f"  GET  http://{host}:{port}/api/schedule/metrics")
    logger.info(f"  GET  http://{host}:{port}/api/schedule/tasks")
    logger.info(f"  GET  http://{host}:{port}/api/schedule/utilization")
    logger.info(f"  GET  http://{host}:{port}/api/schedule/lateness")
    app.run(host=host, port=port, debug=debug, use_reloader=False)


if __name__ == "__main__":
    # Example: Run with sample data
    sample_result = {
        "status": "success",
        "scheduled_tasks": [],
        "quality_metrics": {},
        "statistics": {},
        "gantt_data": {},
    }
    run_api_server(sample_result, debug=True)

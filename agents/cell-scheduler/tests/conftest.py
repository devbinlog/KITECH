"""Pytest configuration and fixtures for cell-scheduler tests.

WorkOrder contains operations directly (no Job layer).
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add paths for imports - must use the package properly
workspace = Path(__file__).parent.parent.parent.parent
src_path = workspace / "agents" / "cell-scheduler" / "src"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(workspace / "shared"))

from solvers import WorkOrder, Operation, Machine, NcCode  # noqa: E402
from cell_scheduler_agent import CellSchedulerAgent, DataLoader  # noqa: E402


@pytest.fixture
def input_directory():
    """Get scheduling input directory."""
    return workspace / "samples" / "cell-scheduler" / "input"


@pytest.fixture
def scheduler_agent():
    """Create scheduler agent instance."""
    return CellSchedulerAgent()


@pytest.fixture
def scheduling_data(input_directory):
    """Load scheduling data from samples."""
    loader = DataLoader(str(input_directory))
    return loader.load_all()


@pytest.fixture
def minimal_nc_code():
    """Create minimal NC code for testing."""
    return NcCode(
        program_id="NC001",
        file_path="/test/program.nc",
        cycle_time_sec=60,
        cycle_time_confidence=0.95,
        tool_list=["T01", "T02"],
        tool_change_count=2,
        compatible_machines=["M1", "M2"],
    )


@pytest.fixture
def minimal_operation(minimal_nc_code):
    """Create minimal operation for testing."""
    return Operation(
        op_id="OP001",
        op_name="Test Operation",
        sequence=1,
        predecessors=[],
        required_machines=["CNC"],
        setup_id="SETUP001",
        nc_code=minimal_nc_code,
    )


@pytest.fixture
def minimal_work_order(minimal_operation):
    """Create minimal work order for testing (operations directly)."""
    return WorkOrder(
        wo_id="WO001",
        product_id="PROD001",
        product_name="Test Product",
        order_quantity=100,
        due_date=datetime.now(timezone.utc) + timedelta(days=7),
        priority=5,
        release_date=datetime.now(timezone.utc),
        customer="Test Customer",
        operations=[minimal_operation],
    )


@pytest.fixture
def minimal_machine():
    """Create minimal machine for testing."""
    return Machine(
        machine_id="M001",
        machine_name="CNC Machine 1",
        machine_type="CNC",
        status="available",
        available_from=datetime.now(timezone.utc),
        current_setup_id=None,
        setup_change_time_min=10,
    )

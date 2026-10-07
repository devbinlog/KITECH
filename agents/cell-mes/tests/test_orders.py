"""Tests for work order state machine and payload generation."""

import pytest
from src.app.models.production import WorkOrder


class TestWorkOrderStateMachine:
    """Test work order state transitions."""

    def test_can_transition_from_ready_to_running(self):
        """Work order can start from READY state."""
        order = WorkOrder(
            lot_no="TEST-001",
            product_id=1,
            target_qty=100,
            status="READY",
        )

        assert order.can_transition_to("RUNNING") is True
        assert order.can_transition_to("SCHEDULED") is True
        assert order.can_transition_to("PAUSE") is False
        assert order.can_transition_to("DONE") is False
        assert order.can_transition_to("ERROR") is False

    def test_transition_ready_to_scheduled(self):
        """Work order can be scheduled from READY state."""
        order = WorkOrder(
            lot_no="TEST-001",
            product_id=1,
            target_qty=100,
            status="READY",
        )
        assert order.can_transition_to("SCHEDULED") is True

    def test_transition_scheduled_to_running(self):
        """Scheduled work order can start running."""
        order = WorkOrder(
            lot_no="TEST-001",
            product_id=1,
            target_qty=100,
            status="SCHEDULED",
        )
        assert order.can_transition_to("RUNNING") is True

    def test_transition_scheduled_to_cancel(self):
        """Scheduled work order can be cancelled."""
        order = WorkOrder(
            lot_no="TEST-001",
            product_id=1,
            target_qty=100,
            status="SCHEDULED",
        )
        assert order.can_transition_to("CANCEL") is True

    def test_transition_scheduled_to_done_blocked(self):
        """Scheduled work order cannot jump directly to DONE."""
        order = WorkOrder(
            lot_no="TEST-001",
            product_id=1,
            target_qty=100,
            status="SCHEDULED",
        )
        assert order.can_transition_to("DONE") is False

    def test_transition_scheduled_to_pause_blocked(self):
        """Scheduled work order cannot transition to PAUSE."""
        order = WorkOrder(
            lot_no="TEST-001",
            product_id=1,
            target_qty=100,
            status="SCHEDULED",
        )
        assert order.can_transition_to("PAUSE") is False

    def test_can_transition_from_running(self):
        """Work order can pause, complete, or error from RUNNING state."""
        order = WorkOrder(
            lot_no="TEST-001",
            product_id=1,
            target_qty=100,
            status="RUNNING",
        )

        assert order.can_transition_to("PAUSE") is True
        assert order.can_transition_to("DONE") is True
        assert order.can_transition_to("ERROR") is True
        assert order.can_transition_to("READY") is False

    def test_can_transition_from_pause(self):
        """Work order can resume or complete from PAUSE state."""
        order = WorkOrder(
            lot_no="TEST-001",
            product_id=1,
            target_qty=100,
            status="PAUSE",
        )

        assert order.can_transition_to("RUNNING") is True
        assert order.can_transition_to("DONE") is True
        assert order.can_transition_to("ERROR") is False

    def test_can_transition_from_error(self):
        """Work order can resume or complete from ERROR state."""
        order = WorkOrder(
            lot_no="TEST-001",
            product_id=1,
            target_qty=100,
            status="ERROR",
        )

        assert order.can_transition_to("RUNNING") is True
        assert order.can_transition_to("DONE") is True
        assert order.can_transition_to("PAUSE") is False

    def test_cannot_transition_from_done(self):
        """Work order cannot transition from DONE state."""
        order = WorkOrder(
            lot_no="TEST-001",
            product_id=1,
            target_qty=100,
            status="DONE",
        )

        assert order.can_transition_to("RUNNING") is False
        assert order.can_transition_to("PAUSE") is False
        assert order.can_transition_to("ERROR") is False
        assert order.can_transition_to("READY") is False

    def test_invalid_transition_is_rejected(self):
        """Invalid status transitions are rejected."""
        order = WorkOrder(
            lot_no="TEST-001",
            product_id=1,
            target_qty=100,
            status="READY",
        )

        # Can't go directly from READY to DONE
        assert order.can_transition_to("DONE") is False

        # Can't go to invalid status
        assert order.can_transition_to("INVALID") is False


class TestWorkOrderValidTransitions:
    """Test all valid state transition paths."""

    @pytest.mark.parametrize(
        "current,expected_valid",
        [
            ("READY", ["SCHEDULED", "RUNNING"]),
            ("SCHEDULED", ["RUNNING"]),
            ("RUNNING", ["PAUSE", "DONE", "ERROR"]),
            ("PAUSE", ["RUNNING", "DONE"]),
            ("ERROR", ["RUNNING", "DONE"]),
            ("DONE", []),
        ],
    )
    def test_valid_transitions(self, current, expected_valid):
        """Test valid transitions for each state."""
        order = WorkOrder(
            lot_no="TEST-001",
            product_id=1,
            target_qty=100,
            status=current,
        )

        # Check expected valid transitions
        for status in expected_valid:
            assert order.can_transition_to(status) is True, f"Should allow {current} -> {status}"

        # Check that all other transitions are invalid
        all_statuses = {"READY", "SCHEDULED", "RUNNING", "PAUSE", "DONE", "ERROR"}
        invalid_statuses = all_statuses - set(expected_valid)
        for status in invalid_statuses:
            if status != current:  # Don't test self-transition
                assert order.can_transition_to(status) is False, (
                    f"Should not allow {current} -> {status}"
                )

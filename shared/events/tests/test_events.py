"""Tests for event models."""

from datetime import datetime

from ..base import Event, EventMetadata
from ..production import (
    WorkOrderCreatedEvent,
    WorkOrderStatusChangedEvent,
    ProductionRecordedEvent,
)
from ..scheduling import ScheduleRequestedEvent, ScheduleCompletedEvent
from ..quality import InspectionCompletedEvent, NCRCreatedEvent


class TestEventMetadata:
    """Tests for EventMetadata."""

    def test_default_values(self):
        """Test that metadata has sensible defaults."""
        meta = EventMetadata()

        assert meta.event_id is not None
        assert len(meta.event_id) > 0
        assert meta.timestamp is not None
        assert meta.version == 1
        assert meta.source_service == ""
        assert meta.correlation_id is None
        assert meta.causation_id is None

    def test_unique_event_ids(self):
        """Test that each metadata gets a unique event ID."""
        meta1 = EventMetadata()
        meta2 = EventMetadata()

        assert meta1.event_id != meta2.event_id


class TestBaseEvent:
    """Tests for base Event class."""

    def test_event_creation(self):
        """Test basic event creation."""
        event = Event()

        assert event.event_type == "base.event"
        assert event.metadata is not None
        assert event.payload == {}

    def test_to_channel(self):
        """Test channel name generation."""
        event = Event(event_type="test.event")

        assert event.to_channel() == "events:test.event"

    def test_with_correlation(self):
        """Test adding correlation ID."""
        event = Event()
        correlated = event.with_correlation("corr-123")

        assert correlated.metadata.correlation_id == "corr-123"
        assert event.metadata.correlation_id is None  # Original unchanged

    def test_with_causation(self):
        """Test adding causation ID."""
        event = Event()
        caused = event.with_causation("cause-456")

        assert caused.metadata.causation_id == "cause-456"
        assert event.metadata.causation_id is None  # Original unchanged

    def test_with_source(self):
        """Test adding source service."""
        event = Event()
        sourced = event.with_source("cell-mes")

        assert sourced.metadata.source_service == "cell-mes"
        assert event.metadata.source_service == ""  # Original unchanged

    def test_json_serialization(self):
        """Test event can be serialized to JSON."""
        event = Event(event_type="test.event", payload={"key": "value"})

        json_str = event.model_dump_json()

        assert "test.event" in json_str
        assert "key" in json_str

    def test_json_deserialization(self):
        """Test event can be deserialized from JSON."""
        event = Event(event_type="test.event", payload={"key": "value"})
        json_str = event.model_dump_json()

        restored = Event.model_validate_json(json_str)

        assert restored.event_type == event.event_type
        assert restored.payload == event.payload


class TestWorkOrderEvents:
    """Tests for work order events."""

    def test_work_order_created(self):
        """Test WorkOrderCreatedEvent."""
        event = WorkOrderCreatedEvent(
            work_order_id=1,
            lot_no="LOT-001",
            product_id=10,
            product_code="PROD-A",
            order_qty=100,
            priority=80,
        )

        assert event.event_type == "work_order.created"
        assert event.work_order_id == 1
        assert event.lot_no == "LOT-001"
        assert event.order_qty == 100
        assert event.to_channel() == "events:work_order.created"

    def test_work_order_status_changed(self):
        """Test WorkOrderStatusChangedEvent."""
        event = WorkOrderStatusChangedEvent(
            work_order_id=1,
            lot_no="LOT-001",
            previous_status="RELEASED",
            new_status="RUNNING",
        )

        assert event.event_type == "work_order.status_changed"
        assert event.previous_status == "RELEASED"
        assert event.new_status == "RUNNING"

    def test_production_recorded(self):
        """Test ProductionRecordedEvent."""
        event = ProductionRecordedEvent(
            work_order_id=1,
            lot_no="LOT-001",
            operation_id=1,
            equipment_id=5,
            equipment_name="CNC-001",
            ok_qty=95,
            ng_qty=5,
            start_time=datetime(2024, 1, 1, 8, 0),
            end_time=datetime(2024, 1, 1, 10, 0),
        )

        assert event.event_type == "production.recorded"
        assert event.ok_qty == 95
        assert event.ng_qty == 5


class TestSchedulingEvents:
    """Tests for scheduling events."""

    def test_schedule_requested(self):
        """Test ScheduleRequestedEvent."""
        event = ScheduleRequestedEvent(
            request_id="req-123",
            horizon_hours=24,
            solver_type="OR_TOOLS",
        )

        assert event.event_type == "schedule.requested"
        assert event.horizon_hours == 24
        assert event.solver_type == "OR_TOOLS"

    def test_schedule_completed(self):
        """Test ScheduleCompletedEvent."""
        event = ScheduleCompletedEvent(
            request_id="req-123",
            success=True,
            solver_type="OR_TOOLS",
            makespan_hours=16.5,
            total_jobs_scheduled=50,
            solve_time_sec=45.2,
        )

        assert event.event_type == "schedule.completed"
        assert event.success is True
        assert event.makespan_hours == 16.5


class TestQualityEvents:
    """Tests for quality events."""

    def test_inspection_completed(self):
        """Test InspectionCompletedEvent."""
        event = InspectionCompletedEvent(
            inspection_id=1,
            work_order_id=1,
            lot_no="LOT-001",
            inspection_type="FIRST_ARTICLE",
            result="PASS",
            sample_size=10,
        )

        assert event.event_type == "inspection.completed"
        assert event.result == "PASS"

    def test_ncr_created(self):
        """Test NCRCreatedEvent."""
        event = NCRCreatedEvent(
            ncr_id=1,
            ncr_number="NCR-2024-001",
            ncr_type="PROCESS",
            severity="MAJOR",
            affected_qty=50,
        )

        assert event.event_type == "ncr.created"
        assert event.ncr_number == "NCR-2024-001"
        assert event.severity == "MAJOR"


class TestEventChaining:
    """Tests for event chaining patterns."""

    def test_correlation_chain(self):
        """Test that events can be correlated."""
        # Initial event
        wo_created = WorkOrderCreatedEvent(
            work_order_id=1,
            lot_no="LOT-001",
            product_id=10,
            product_code="PROD-A",
            order_qty=100,
        )

        # Correlated event
        schedule_requested = ScheduleRequestedEvent(
            request_id="req-001",
            horizon_hours=24,
            solver_type="OR_TOOLS",
        ).with_correlation(wo_created.metadata.event_id)

        assert schedule_requested.metadata.correlation_id == wo_created.metadata.event_id

    def test_causation_chain(self):
        """Test that events can track causation."""
        # Cause event
        inspection = InspectionCompletedEvent(
            inspection_id=1,
            work_order_id=1,
            lot_no="LOT-001",
            inspection_type="FINAL",
            result="FAIL",
        )

        # Effect event
        ncr = NCRCreatedEvent(
            ncr_id=1,
            ncr_number="NCR-001",
            ncr_type="PROCESS",
            severity="MAJOR",
        ).with_causation(inspection.metadata.event_id)

        assert ncr.metadata.causation_id == inspection.metadata.event_id

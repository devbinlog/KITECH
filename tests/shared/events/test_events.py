"""Tests for shared events module."""

from datetime import datetime, timedelta, timezone

from shared.events.base import Event, EventMetadata
from shared.events.production import (
    WorkOrderCreatedEvent,
    WorkOrderStatusChangedEvent,
    ProductionRecordedEvent,
)
from shared.events.scheduling import (
    ScheduleRequestedEvent,
    ScheduleCompletedEvent,
)
from shared.events.quality import (
    InspectionCompletedEvent,
    NCRCreatedEvent,
)


class TestEventMetadata:
    """Tests for EventMetadata."""
    
    def test_metadata_auto_generates_id(self):
        metadata = EventMetadata()
        assert metadata.event_id is not None
        assert len(metadata.event_id) == 36  # UUID length
    
    def test_metadata_auto_generates_timestamp(self):
        metadata = EventMetadata()
        assert metadata.timestamp is not None
        assert isinstance(metadata.timestamp, datetime)
    
    def test_metadata_with_correlation_id(self):
        metadata = EventMetadata(
            correlation_id="corr-123",
            causation_id="cause-456",
        )
        assert metadata.correlation_id == "corr-123"
        assert metadata.causation_id == "cause-456"


class TestEvent:
    """Tests for base Event."""
    
    def test_event_creates_metadata_automatically(self):
        event = Event()
        assert event.metadata is not None
        assert event.metadata.event_id is not None
    
    def test_event_to_channel(self):
        event = Event(event_type="test.event")
        assert event.to_channel() == "events:test.event"
    
    def test_event_with_correlation(self):
        event = Event()
        correlated = event.with_correlation("corr-123")
        assert correlated.metadata.correlation_id == "corr-123"
    
    def test_event_with_source(self):
        event = Event()
        sourced = event.with_source("test-service")
        assert sourced.metadata.source_service == "test-service"


class TestWorkOrderCreatedEvent:
    """Tests for WorkOrderCreatedEvent."""
    
    def test_create_work_order_event(self):
        event = WorkOrderCreatedEvent(
            work_order_id=1,
            lot_no="LOT-001",
            product_id=10,
            product_code="WIDGET-A",
            order_qty=100,
            priority=80,
        )
        
        assert event.work_order_id == 1
        assert event.lot_no == "LOT-001"
        assert event.order_qty == 100
        assert event.priority == 80
        assert event.event_type == "work_order.created"
    
    def test_event_channel(self):
        event = WorkOrderCreatedEvent(
            work_order_id=1,
            lot_no="LOT-001",
            product_id=10,
            product_code="WIDGET",
            order_qty=100,
        )
        assert event.to_channel() == "events:work_order.created"
    
    def test_serialization(self):
        event = WorkOrderCreatedEvent(
            work_order_id=1,
            lot_no="LOT-001",
            product_id=10,
            product_code="WIDGET",
            order_qty=100,
            due_date=datetime(2024, 12, 31, 23, 59, 59),
        )
        
        json_str = event.model_dump_json()
        restored = WorkOrderCreatedEvent.model_validate_json(json_str)
        
        assert restored.work_order_id == 1
        assert restored.lot_no == "LOT-001"


class TestWorkOrderStatusChangedEvent:
    """Tests for WorkOrderStatusChangedEvent."""
    
    def test_status_change_event(self):
        event = WorkOrderStatusChangedEvent(
            work_order_id=1,
            lot_no="LOT-001",
            previous_status="READY",
            new_status="RUNNING",
        )
        
        assert event.previous_status == "READY"
        assert event.new_status == "RUNNING"
        assert event.event_type == "work_order.status_changed"


class TestProductionRecordedEvent:
    """Tests for ProductionRecordedEvent."""
    
    def test_production_recorded_event(self):
        now = datetime.now(timezone.utc)
        event = ProductionRecordedEvent(
            work_order_id=1,
            lot_no="LOT-001",
            operation_id=1,
            equipment_id=5,
            equipment_name="CNC-01",
            ok_qty=95,
            ng_qty=5,
            start_time=now - timedelta(hours=1),
            end_time=now,
        )
        
        assert event.ok_qty == 95
        assert event.ng_qty == 5
        assert event.event_type == "production.recorded"


class TestSchedulingEvents:
    """Tests for scheduling events."""
    
    def test_schedule_requested_event(self):
        event = ScheduleRequestedEvent(
            request_id="REQ-001",
            horizon_hours=24,
        )
        
        assert event.request_id == "REQ-001"
        assert event.event_type == "schedule.requested"
    
    def test_schedule_completed_event(self):
        event = ScheduleCompletedEvent(
            request_id="REQ-001",
            success=True,
            solver_type="OR_TOOLS",
            total_jobs_scheduled=10,
            makespan_hours=48.5,
        )
        
        assert event.success is True
        assert event.total_jobs_scheduled == 10


class TestQualityEvents:
    """Tests for quality events."""
    
    def test_inspection_completed_event(self):
        event = InspectionCompletedEvent(
            inspection_id=1,
            work_order_id=1,
            lot_no="LOT-001",
            inspection_type="FINAL",
            result="PASS",
            sample_size=100,
            defects_found=2,
        )
        
        assert event.result == "PASS"
        assert event.sample_size == 100
    
    def test_ncr_created_event(self):
        event = NCRCreatedEvent(
            ncr_id=1,
            ncr_number="NCR-001",
            work_order_id=1,
            lot_no="LOT-001",
            ncr_type="PROCESS",
            affected_qty=5,
            severity="MAJOR",
        )
        
        assert event.ncr_type == "PROCESS"
        assert event.severity == "MAJOR"

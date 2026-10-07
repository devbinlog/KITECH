"""
Quality domain events.

Events related to quality inspection and non-conformance.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import ConfigDict, Field

from .base import Event


class InspectionCompletedEvent(Event):
    """
    Published when a quality inspection is completed.

    Consumers:
    - Production: Update lot status
    - Analytics: Track quality metrics
    - NCR: Create NCR if inspection failed
    """

    model_config = ConfigDict(frozen=True)
    event_type: str = "inspection.completed"

    inspection_id: int
    work_order_id: int
    lot_no: str
    operation_id: Optional[int] = None

    # Inspection details
    inspection_type: str  # "FIRST_ARTICLE", "IN_PROCESS", "FINAL"
    inspector_id: Optional[str] = None

    # Results
    result: str  # "PASS", "FAIL", "CONDITIONAL"
    sample_size: int = 0
    defects_found: int = 0

    # Measurements
    measurements: Dict[str, Any] = Field(default_factory=dict)
    out_of_spec_items: List[str] = Field(default_factory=list)

    # Timing
    inspected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NCRCreatedEvent(Event):
    """
    Published when a Non-Conformance Report (NCR) is created.

    NCRs are created when:
    - Inspection fails
    - Customer complaint received
    - Internal quality issue discovered

    Consumers:
    - Quality Team: Review and disposition
    - Production: May need to hold affected lots
    - Analytics: Track NCR trends
    """

    model_config = ConfigDict(frozen=True)
    event_type: str = "ncr.created"

    ncr_id: int
    ncr_number: str

    # Related entities
    work_order_id: Optional[int] = None
    lot_no: Optional[str] = None
    product_id: Optional[int] = None
    equipment_id: Optional[int] = None

    # NCR details
    ncr_type: str  # "MATERIAL", "PROCESS", "DESIGN", "CUSTOMER"
    severity: str = "MINOR"  # "MINOR", "MAJOR", "CRITICAL"
    description: str = ""

    # Quantities
    affected_qty: int = 0

    # Source
    source: str = "INSPECTION"  # "INSPECTION", "CUSTOMER", "INTERNAL"
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NCRDispositionedEvent(Event):
    """
    Published when an NCR disposition decision is made.

    Dispositions:
    - USE_AS_IS: Accept the non-conformance
    - REWORK: Rework to meet specifications
    - SCRAP: Discard affected items
    - RETURN: Return to supplier

    Consumers:
    - Production: Execute disposition action
    - Inventory: Update stock if scrapped
    """

    model_config = ConfigDict(frozen=True)
    event_type: str = "ncr.dispositioned"

    ncr_id: int
    ncr_number: str

    disposition: str  # "USE_AS_IS", "REWORK", "SCRAP", "RETURN"
    disposition_qty: int = 0
    disposition_notes: str = ""

    approved_by: Optional[str] = None
    dispositioned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DefectCodeRecordedEvent(Event):
    """
    Published when a defect code is recorded during production.

    Consumers:
    - Quality: Track defect trends
    - Analytics: Pareto analysis
    """

    model_config = ConfigDict(frozen=True)
    event_type: str = "defect.recorded"

    work_order_id: int
    lot_no: str
    operation_id: int
    equipment_id: int

    defect_code: str
    defect_description: str = ""
    quantity: int = 1

    recorded_by: Optional[str] = None
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

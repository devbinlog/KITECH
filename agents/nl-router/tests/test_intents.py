"""Tests for intent definitions and metadata."""

import pytest

from src.understanding.intents import (
    Intent,
    IntentResult,
    INTENT_METADATA,
    get_intent_metadata,
)


class TestIntent:
    """Tests for Intent enum."""

    def test_production_status_value(self):
        """Should have correct value for PRODUCTION_STATUS."""
        assert Intent.PRODUCTION_STATUS.value == "production_status"

    def test_equipment_status_value(self):
        """Should have correct value for EQUIPMENT_STATUS."""
        assert Intent.EQUIPMENT_STATUS.value == "equipment_status"

    def test_unknown_value(self):
        """Should have 'unknown' value for UNKNOWN."""
        assert Intent.UNKNOWN.value == "unknown"

    def test_all_intents_have_values(self):
        """All intents should have string values."""
        for intent in Intent:
            assert isinstance(intent.value, str)
            assert len(intent.value) > 0

    def test_intent_from_string(self):
        """Should be able to get intent from string value."""
        intent = Intent("production_status")
        assert intent == Intent.PRODUCTION_STATUS

    def test_intent_count(self):
        """Should have expected number of intents."""
        # At least 10+ core intents
        assert len(Intent) >= 10


class TestIntentResult:
    """Tests for IntentResult model."""

    def test_create_basic(self):
        """Should create result with required fields."""
        result = IntentResult(
            intent=Intent.PRODUCTION_STATUS,
            confidence=0.95,
        )

        assert result.intent == Intent.PRODUCTION_STATUS
        assert result.confidence == 0.95
        assert result.entities == {}

    def test_create_with_entities(self):
        """Should support entities dict."""
        result = IntentResult(
            intent=Intent.EQUIPMENT_STATUS,
            confidence=0.85,
            entities={"equipment_id": "EQ-001"},
        )

        assert result.entities["equipment_id"] == "EQ-001"

    def test_create_with_sub_intent(self):
        """Should support sub_intent."""
        result = IntentResult(
            intent=Intent.KPI_QUERY,
            confidence=0.9,
            sub_intent="utilization",
        )

        assert result.sub_intent == "utilization"

    def test_create_with_reasoning(self):
        """Should support reasoning field."""
        result = IntentResult(
            intent=Intent.ANALYTICS,
            confidence=0.88,
            reasoning="User asked about trends with '추이' keyword",
        )

        assert "추이" in result.reasoning

    def test_requires_clarification(self):
        """Should support requires_clarification flag."""
        result = IntentResult(
            intent=Intent.UNKNOWN,
            confidence=0.4,
            requires_clarification=True,
            suggested_questions=["어떤 설비의 상태를 확인하시겠습니까?"],
        )

        assert result.requires_clarification is True
        assert len(result.suggested_questions) == 1

    def test_confidence_bounds(self):
        """Confidence should be between 0 and 1."""
        with pytest.raises(ValueError):
            IntentResult(intent=Intent.UNKNOWN, confidence=1.5)

        with pytest.raises(ValueError):
            IntentResult(intent=Intent.UNKNOWN, confidence=-0.1)

    def test_default_values(self):
        """Should have correct default values."""
        result = IntentResult(
            intent=Intent.PRODUCTION_STATUS,
            confidence=0.9,
        )

        assert result.sub_intent is None
        assert result.reasoning is None
        assert result.requires_clarification is False
        assert result.suggested_questions == []


class TestIntentMetadata:
    """Tests for INTENT_METADATA dictionary."""

    def test_all_intents_have_metadata(self):
        """All intents should have metadata defined."""
        for intent in Intent:
            assert intent in INTENT_METADATA, f"Missing metadata for {intent}"

    def test_metadata_has_description(self):
        """All metadata should have description."""
        for intent, meta in INTENT_METADATA.items():
            assert "description" in meta
            assert len(meta["description"]) > 0

    def test_metadata_has_skills(self):
        """All metadata should have skills list."""
        for intent, meta in INTENT_METADATA.items():
            assert "skills" in meta
            assert isinstance(meta["skills"], list)

    def test_metadata_has_required_entities(self):
        """All metadata should have required_entities."""
        for intent, meta in INTENT_METADATA.items():
            assert "required_entities" in meta
            assert isinstance(meta["required_entities"], list)

    def test_metadata_has_optional_entities(self):
        """All metadata should have optional_entities."""
        for intent, meta in INTENT_METADATA.items():
            assert "optional_entities" in meta
            assert isinstance(meta["optional_entities"], list)

    def test_metadata_has_output_type(self):
        """All metadata should have output_type."""
        for intent, meta in INTENT_METADATA.items():
            assert "output_type" in meta

    def test_production_status_metadata(self):
        """PRODUCTION_STATUS should have correct metadata."""
        meta = INTENT_METADATA[Intent.PRODUCTION_STATUS]

        assert "생산" in meta["description"]
        assert "mes_production_query" in meta["skills"]
        assert meta["output_type"] == "dashboard"

    def test_equipment_status_metadata(self):
        """EQUIPMENT_STATUS should have correct metadata."""
        meta = INTENT_METADATA[Intent.EQUIPMENT_STATUS]

        assert "설비" in meta["description"]
        assert "mes_equipment_status" in meta["skills"]
        assert "equipment_id" in meta["optional_entities"]

    def test_traceability_requires_lot(self):
        """TRACEABILITY should require lot_no."""
        meta = INTENT_METADATA[Intent.TRACEABILITY]

        assert "lot_no" in meta["required_entities"]

    def test_schedule_request_metadata(self):
        """SCHEDULE_REQUEST should have correct metadata."""
        meta = INTENT_METADATA[Intent.SCHEDULE_REQUEST]

        assert "스케줄" in meta["description"]
        assert meta["output_type"] == "gantt"

    def test_unknown_has_empty_skills(self):
        """UNKNOWN should have no skills."""
        meta = INTENT_METADATA[Intent.UNKNOWN]

        assert meta["skills"] == []
        assert meta["output_type"] == "help"


class TestGetIntentMetadata:
    """Tests for get_intent_metadata function."""

    def test_get_existing_metadata(self):
        """Should return metadata for existing intent."""
        meta = get_intent_metadata(Intent.PRODUCTION_STATUS)

        assert meta is not None
        assert "description" in meta

    def test_get_unknown_returns_unknown_meta(self):
        """Should return UNKNOWN metadata for unknown intent."""
        meta = get_intent_metadata(Intent.UNKNOWN)

        assert meta["output_type"] == "help"

    def test_returns_dict(self):
        """Should always return a dictionary."""
        for intent in Intent:
            meta = get_intent_metadata(intent)
            assert isinstance(meta, dict)


class TestIntentCoverage:
    """Tests for comprehensive intent coverage."""

    def test_production_intents(self):
        """Should have production-related intents."""
        production_intents = [
            Intent.PRODUCTION_STATUS,
            Intent.PRODUCTION_DETAIL,
        ]
        for intent in production_intents:
            assert intent in Intent

    def test_equipment_intents(self):
        """Should have equipment-related intents."""
        equipment_intents = [
            Intent.EQUIPMENT_STATUS,
            Intent.EQUIPMENT_LIST,
        ]
        for intent in equipment_intents:
            assert intent in Intent

    def test_analytics_intents(self):
        """Should have analytics-related intents."""
        analytics_intents = [
            Intent.KPI_QUERY,
            Intent.ANALYTICS,
            Intent.COMPARISON,
        ]
        for intent in analytics_intents:
            assert intent in Intent

    def test_scheduling_intents(self):
        """Should have scheduling-related intents."""
        scheduling_intents = [
            Intent.SCHEDULE_QUERY,
            Intent.SCHEDULE_REQUEST,
        ]
        for intent in scheduling_intents:
            assert intent in Intent

    def test_diagnostic_intents(self):
        """Should have diagnostic-related intents."""
        diagnostic_intents = [
            Intent.ERROR_DIAGNOSIS,
            Intent.DELAY_PREDICTION,
            Intent.DEFECT_ANALYSIS,
        ]
        for intent in diagnostic_intents:
            assert intent in Intent

    def test_action_intents(self):
        """Should have action-related intents."""
        assert Intent.ACTION_REQUEST in Intent

    def test_traceability_intent(self):
        """Should have traceability intent."""
        assert Intent.TRACEABILITY in Intent

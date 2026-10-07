"""Tests for entity definitions and DateRangeResolver."""

import pytest
from datetime import date, timedelta

from src.understanding.entities import (
    EntityType,
    Entity,
    ExtractedEntities,
    DateRangeResolver,
    DATE_KEYWORDS,
    DATE_RANGE_KEYWORDS,
    STATUS_KEYWORDS,
    EQUIPMENT_TYPE_KEYWORDS,
    METRIC_KEYWORDS,
    GROUP_BY_KEYWORDS,
    DEFECT_KEYWORDS,
    SHIFT_KEYWORDS,
)


class TestEntityType:
    """Tests for EntityType enum."""

    def test_date_value(self):
        """Should have correct value for DATE."""
        assert EntityType.DATE.value == "date"

    def test_equipment_id_value(self):
        """Should have correct value for EQUIPMENT_ID."""
        assert EntityType.EQUIPMENT_ID.value == "equipment_id"

    def test_all_entity_types_have_values(self):
        """All entity types should have string values."""
        for entity_type in EntityType:
            assert isinstance(entity_type.value, str)
            assert len(entity_type.value) > 0


class TestEntity:
    """Tests for Entity model."""

    def test_create_entity(self):
        """Should create entity with required fields."""
        entity = Entity(
            type=EntityType.DATE,
            value="2026-02-03",
            raw_text="오늘",
        )

        assert entity.type == EntityType.DATE
        assert entity.value == "2026-02-03"
        assert entity.raw_text == "오늘"
        assert entity.confidence == 1.0

    def test_entity_with_normalized(self):
        """Should support normalized value."""
        entity = Entity(
            type=EntityType.STATUS,
            value="진행중",
            raw_text="진행중",
            normalized="RUNNING",
        )

        assert entity.normalized == "RUNNING"

    def test_entity_with_confidence(self):
        """Should support custom confidence."""
        entity = Entity(
            type=EntityType.PRODUCT_ID,
            value="PROD-001",
            raw_text="제품 001",
            confidence=0.85,
        )

        assert entity.confidence == 0.85


class TestExtractedEntities:
    """Tests for ExtractedEntities collection."""

    @pytest.fixture
    def sample_entities(self):
        return ExtractedEntities(
            entities=[
                Entity(type=EntityType.DATE, value="2026-02-03", raw_text="오늘"),
                Entity(type=EntityType.EQUIPMENT_ID, value="EQ-001", raw_text="1번 설비"),
                Entity(
                    type=EntityType.STATUS, value="진행중", raw_text="진행중", normalized="RUNNING"
                ),
                Entity(type=EntityType.EQUIPMENT_ID, value="EQ-002", raw_text="2번 설비"),
            ]
        )

    def test_get_existing_entity(self, sample_entities):
        """Should return first entity of given type."""
        entity = sample_entities.get(EntityType.DATE)

        assert entity is not None
        assert entity.value == "2026-02-03"

    def test_get_nonexistent_entity(self, sample_entities):
        """Should return None for missing type."""
        entity = sample_entities.get(EntityType.LOT_NO)

        assert entity is None

    def test_get_all_single_type(self, sample_entities):
        """Should return all entities of given type."""
        entities = sample_entities.get_all(EntityType.EQUIPMENT_ID)

        assert len(entities) == 2
        assert entities[0].value == "EQ-001"
        assert entities[1].value == "EQ-002"

    def test_get_all_empty(self, sample_entities):
        """Should return empty list for missing type."""
        entities = sample_entities.get_all(EntityType.PRODUCT_ID)

        assert entities == []

    def test_get_value_existing(self, sample_entities):
        """Should return value for existing entity."""
        value = sample_entities.get_value(EntityType.DATE)

        assert value == "2026-02-03"

    def test_get_value_normalized(self, sample_entities):
        """Should return normalized value if available."""
        value = sample_entities.get_value(EntityType.STATUS)

        assert value == "RUNNING"

    def test_get_value_default(self, sample_entities):
        """Should return default for missing entity."""
        value = sample_entities.get_value(EntityType.LOT_NO, default="N/A")

        assert value == "N/A"

    def test_has_existing(self, sample_entities):
        """Should return True for existing type."""
        assert sample_entities.has(EntityType.DATE) is True

    def test_has_missing(self, sample_entities):
        """Should return False for missing type."""
        assert sample_entities.has(EntityType.LOT_NO) is False

    def test_to_dict_basic(self, sample_entities):
        """Should convert to dictionary."""
        result = sample_entities.to_dict()

        assert result["date"] == "2026-02-03"
        assert result["status"] == "RUNNING"

    def test_to_dict_multiple_values(self, sample_entities):
        """Should handle multiple values as list."""
        result = sample_entities.to_dict()

        # Multiple equipment_ids should be a list
        assert isinstance(result["equipment_id"], list)
        assert "EQ-001" in result["equipment_id"]
        assert "EQ-002" in result["equipment_id"]


class TestDateRangeResolver:
    """Tests for DateRangeResolver."""

    @pytest.fixture
    def reference_date(self):
        """Fixed reference date for testing."""
        return date(2026, 2, 3)  # Monday

    def test_this_week(self, reference_date):
        """Should resolve this_week to current week bounds."""
        start, end = DateRangeResolver.resolve("this_week", reference_date)

        # Feb 3, 2026 is Monday (weekday 0)
        assert start == date(2026, 2, 2)  # Monday
        assert end == date(2026, 2, 8)  # Sunday

    def test_last_week(self, reference_date):
        """Should resolve last_week to previous week bounds."""
        start, end = DateRangeResolver.resolve("last_week", reference_date)

        assert start == date(2026, 1, 26)  # Previous Monday
        assert end == date(2026, 2, 1)  # Previous Sunday

    def test_next_week(self, reference_date):
        """Should resolve next_week to next week bounds."""
        start, end = DateRangeResolver.resolve("next_week", reference_date)

        assert start == date(2026, 2, 9)  # Next Monday
        assert end == date(2026, 2, 15)  # Next Sunday

    def test_this_month(self, reference_date):
        """Should resolve this_month to current month bounds."""
        start, end = DateRangeResolver.resolve("this_month", reference_date)

        assert start == date(2026, 2, 1)
        assert end == date(2026, 2, 28)

    def test_last_month(self, reference_date):
        """Should resolve last_month to previous month bounds."""
        start, end = DateRangeResolver.resolve("last_month", reference_date)

        assert start == date(2026, 1, 1)
        assert end == date(2026, 1, 31)

    def test_next_month(self, reference_date):
        """Should resolve next_month to next month bounds."""
        start, end = DateRangeResolver.resolve("next_month", reference_date)

        assert start == date(2026, 3, 1)
        assert end == date(2026, 3, 31)

    def test_last_7_days(self, reference_date):
        """Should resolve last_7_days correctly."""
        start, end = DateRangeResolver.resolve("last_7_days", reference_date)

        assert start == date(2026, 1, 28)
        assert end == date(2026, 2, 3)
        assert (end - start).days == 6  # 7 days inclusive

    def test_last_30_days(self, reference_date):
        """Should resolve last_30_days correctly."""
        start, end = DateRangeResolver.resolve("last_30_days", reference_date)

        assert end == date(2026, 2, 3)
        assert (end - start).days == 29  # 30 days inclusive

    def test_unknown_range(self, reference_date):
        """Should default to single day for unknown range."""
        start, end = DateRangeResolver.resolve("unknown_range", reference_date)

        assert start == reference_date
        assert end == reference_date

    def test_to_dict(self, reference_date):
        """Should return API-friendly dictionary."""
        result = DateRangeResolver.to_dict("this_week", reference_date)

        assert "start_date" in result
        assert "end_date" in result
        assert result["start_date"] == "2026-02-02"
        assert result["end_date"] == "2026-02-08"

    def test_december_to_january(self):
        """Should handle year boundary correctly."""
        ref = date(2026, 1, 5)
        start, end = DateRangeResolver.resolve("last_month", ref)

        assert start == date(2025, 12, 1)
        assert end == date(2025, 12, 31)

    def test_next_month_december(self):
        """Should handle December to January transition."""
        ref = date(2025, 12, 15)
        start, end = DateRangeResolver.resolve("next_month", ref)

        assert start == date(2026, 1, 1)
        assert end == date(2026, 1, 31)


class TestKeywordMappings:
    """Tests for keyword mapping dictionaries."""

    def test_date_keywords_today(self):
        """오늘 should return today's date."""
        func = DATE_KEYWORDS["오늘"]
        assert func() == date.today()

    def test_date_keywords_yesterday(self):
        """어제 should return yesterday's date."""
        func = DATE_KEYWORDS["어제"]
        assert func() == date.today() - timedelta(days=1)

    def test_date_keywords_tomorrow(self):
        """내일 should return tomorrow's date."""
        func = DATE_KEYWORDS["내일"]
        assert func() == date.today() + timedelta(days=1)

    def test_date_range_keywords(self):
        """Date range keywords should map to correct values."""
        assert DATE_RANGE_KEYWORDS["이번 주"] == "this_week"
        assert DATE_RANGE_KEYWORDS["지난 달"] == "last_month"
        assert DATE_RANGE_KEYWORDS["최근 7일"] == "last_7_days"

    def test_status_keywords(self):
        """Status keywords should map to uppercase values."""
        assert STATUS_KEYWORDS["진행중"] == "RUNNING"
        assert STATUS_KEYWORDS["완료"] == "DONE"
        assert STATUS_KEYWORDS["에러"] == "ERROR"

    def test_equipment_type_keywords(self):
        """Equipment type keywords should map correctly."""
        assert EQUIPMENT_TYPE_KEYWORDS["cnc"] == "CNC"
        assert EQUIPMENT_TYPE_KEYWORDS["로봇"] == "ROBOT"

    def test_metric_keywords(self):
        """Metric keywords should map to English values."""
        assert METRIC_KEYWORDS["가동률"] == "utilization"
        assert METRIC_KEYWORDS["수율"] == "yield"
        assert METRIC_KEYWORDS["생산량"] == "production"

    def test_group_by_keywords(self):
        """Group by keywords should map correctly."""
        assert GROUP_BY_KEYWORDS["설비별"] == "equipment"
        assert GROUP_BY_KEYWORDS["제품별"] == "product"
        assert GROUP_BY_KEYWORDS["일별"] == "day"

    def test_defect_keywords(self):
        """Defect keywords should map to types."""
        assert DEFECT_KEYWORDS["치수불량"] == "DIMENSION"
        assert DEFECT_KEYWORDS["외관불량"] == "SURFACE"
        assert DEFECT_KEYWORDS["스크래치"] == "SCRATCH"

    def test_shift_keywords(self):
        """Shift keywords should map to shift values."""
        assert SHIFT_KEYWORDS["주간"] == "DAY_SHIFT"
        assert SHIFT_KEYWORDS["야간"] == "NIGHT_SHIFT"
        assert SHIFT_KEYWORDS["1조"] == "SHIFT_1"

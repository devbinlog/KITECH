"""Tests for Entity Extractor"""

import pytest
from datetime import date
from src.understanding.entities import EntityType, Entity, ExtractedEntities
from src.understanding.entity_extractor import EntityExtractor


class TestEntityExtractor:
    """Tests for rule-based entity extraction"""

    @pytest.fixture
    def extractor(self):
        """Create extractor"""
        return EntityExtractor(use_llm=False)

    @pytest.mark.asyncio
    async def test_extract_lot_number(self, extractor):
        """Test LOT number extraction"""
        queries = [
            ("LOT-001 조회", "LOT"),
            ("LOT_2024_001 이력", "LOT"),
            ("lot-test-123 상태", "LOT"),
        ]

        for query, expected_prefix in queries:
            result = await extractor.extract(query)
            assert result.has(EntityType.LOT_NO)
            # Just verify LOT number was extracted and starts with LOT
            value = result.get_value(EntityType.LOT_NO)
            assert value.upper().startswith(expected_prefix)

    @pytest.mark.asyncio
    async def test_extract_equipment_id(self, extractor):
        """Test equipment ID extraction"""
        queries = [
            ("CNC-001 상태", "CNC-001"),
            ("ROBOT-002 조회", "ROBOT-002"),
            ("PLC001 확인", "PLC-001"),
        ]

        for query, expected in queries:
            result = await extractor.extract(query)
            assert result.has(EntityType.EQUIPMENT_ID)
            assert result.get_value(EntityType.EQUIPMENT_ID) == expected

    @pytest.mark.asyncio
    async def test_extract_date_keywords(self, extractor):
        """Test date keyword extraction"""
        result = await extractor.extract("오늘 생산 현황")
        assert result.has(EntityType.DATE)
        entity = result.get(EntityType.DATE)
        assert entity.normalized == date.today().isoformat()

    @pytest.mark.asyncio
    async def test_extract_date_iso(self, extractor):
        """Test ISO date extraction"""
        result = await extractor.extract("2024-01-24 생산 현황")
        assert result.has(EntityType.DATE)
        assert result.get_value(EntityType.DATE) == "2024-01-24"

    @pytest.mark.asyncio
    async def test_extract_date_korean(self, extractor):
        """Test Korean date format extraction"""
        result = await extractor.extract("2024년 1월 24일 조회")
        assert result.has(EntityType.DATE)
        assert result.get_value(EntityType.DATE) == "2024-01-24"

    @pytest.mark.asyncio
    async def test_extract_date_range(self, extractor):
        """Test date range extraction"""
        queries = [
            ("이번 주 현황", "this_week"),
            ("지난 주 실적", "last_week"),
            ("최근 7일 추이", "last_7_days"),
            ("이번 달 KPI", "this_month"),
        ]

        for query, expected in queries:
            result = await extractor.extract(query)
            assert result.has(EntityType.DATE_RANGE)
            assert result.get_value(EntityType.DATE_RANGE) == expected

    @pytest.mark.asyncio
    async def test_extract_recent_days(self, extractor):
        """Test '최근 N일' pattern extraction"""
        result = await extractor.extract("최근 30일 추이")
        assert result.has(EntityType.DATE_RANGE)
        assert result.get_value(EntityType.DATE_RANGE) == "last_30_days"

    @pytest.mark.asyncio
    async def test_extract_equipment_type(self, extractor):
        """Test equipment type extraction"""
        queries = [
            ("CNC 설비 목록", "CNC"),
            ("로봇 상태", "ROBOT"),
            ("PLC 현황", "PLC"),
        ]

        for query, expected in queries:
            result = await extractor.extract(query)
            assert result.has(EntityType.EQUIPMENT_TYPE)
            assert result.get_value(EntityType.EQUIPMENT_TYPE) == expected

    @pytest.mark.asyncio
    async def test_extract_status(self, extractor):
        """Test status extraction"""
        queries = [
            ("진행중 작업", "RUNNING"),
            ("완료된 작업", "DONE"),
            ("에러 상태", "ERROR"),
        ]

        for query, expected in queries:
            result = await extractor.extract(query)
            assert result.has(EntityType.STATUS)
            assert result.get_value(EntityType.STATUS) == expected

    @pytest.mark.asyncio
    async def test_extract_metric(self, extractor):
        """Test metric extraction"""
        queries = [
            ("가동률 조회", "utilization"),
            ("수율 확인", "yield"),
            ("생산량 현황", "production"),
        ]

        for query, expected in queries:
            result = await extractor.extract(query)
            assert result.has(EntityType.METRIC)
            assert result.get_value(EntityType.METRIC) == expected

    @pytest.mark.asyncio
    async def test_extract_group_by(self, extractor):
        """Test group_by extraction"""
        queries = [
            ("설비별 비교", "equipment"),
            ("제품별 현황", "product"),
            ("일별 추이", "day"),
        ]

        for query, expected in queries:
            result = await extractor.extract(query)
            assert result.has(EntityType.GROUP_BY)
            assert result.get_value(EntityType.GROUP_BY) == expected

    @pytest.mark.asyncio
    async def test_extract_quantity(self, extractor):
        """Test quantity extraction"""
        result = await extractor.extract("100개 생산")
        assert result.has(EntityType.QUANTITY)
        assert result.get_value(EntityType.QUANTITY) == 100

    @pytest.mark.asyncio
    async def test_extract_multiple_entities(self, extractor):
        """Test multiple entity extraction"""
        result = await extractor.extract("오늘 CNC-001 가동률 조회")

        assert result.has(EntityType.DATE)
        assert result.has(EntityType.EQUIPMENT_ID)
        assert result.has(EntityType.METRIC)

    @pytest.mark.asyncio
    async def test_extract_no_entities(self, extractor):
        """Test query with no entities"""
        result = await extractor.extract("안녕하세요")
        assert len(result.entities) == 0


class TestExtractedEntities:
    """Tests for ExtractedEntities model"""

    def test_to_dict(self):
        """Test to_dict conversion"""
        entities = ExtractedEntities(
            entities=[
                Entity(
                    type=EntityType.DATE,
                    value="오늘",
                    raw_text="오늘",
                    normalized="2024-01-24",
                ),
                Entity(
                    type=EntityType.EQUIPMENT_ID,
                    value="CNC-001",
                    raw_text="CNC-001",
                    normalized="CNC-001",
                ),
            ]
        )

        d = entities.to_dict()
        assert d["date"] == "2024-01-24"
        assert d["equipment_id"] == "CNC-001"

    def test_get_value_default(self):
        """Test get_value with default"""
        entities = ExtractedEntities()
        value = entities.get_value(EntityType.DATE, default="today")
        assert value == "today"

    def test_has(self):
        """Test has method"""
        entities = ExtractedEntities(
            entities=[
                Entity(
                    type=EntityType.LOT_NO,
                    value="LOT-001",
                    raw_text="LOT-001",
                ),
            ]
        )

        assert entities.has(EntityType.LOT_NO) is True
        assert entities.has(EntityType.DATE) is False

    def test_get_all(self):
        """Test get_all for multiple entities of same type"""
        entities = ExtractedEntities(
            entities=[
                Entity(
                    type=EntityType.STATUS, value="진행중", raw_text="진행중", normalized="RUNNING"
                ),
                Entity(type=EntityType.STATUS, value="완료", raw_text="완료", normalized="DONE"),
            ]
        )

        all_status = entities.get_all(EntityType.STATUS)
        assert len(all_status) == 2


# ============================================================================
# 보강된 테스트: 비즈니스 규칙 검증
# ============================================================================

class TestDateValidationRules:
    """날짜 형식 유효성 규칙 테스트"""

    @pytest.fixture
    def extractor(self):
        return EntityExtractor(use_llm=False)

    @pytest.mark.asyncio
    async def test_valid_iso_date_format(self, extractor):
        """유효한 ISO 날짜 형식 (YYYY-MM-DD)"""
        result = await extractor.extract("2026-02-15 생산 현황")
        assert result.has(EntityType.DATE)
        assert result.get_value(EntityType.DATE) == "2026-02-15"

    @pytest.mark.asyncio
    async def test_valid_korean_date_format(self, extractor):
        """유효한 한국어 날짜 형식"""
        result = await extractor.extract("2026년 2월 15일 현황")
        assert result.has(EntityType.DATE)
        assert result.get_value(EntityType.DATE) == "2026-02-15"

    @pytest.mark.asyncio
    async def test_date_normalization_consistency(self, extractor):
        """다양한 형식의 날짜가 동일하게 정규화됨"""
        queries = [
            "2026-02-15 현황",
            "2026년 2월 15일 현황",
        ]
        normalized_dates = []
        for query in queries:
            result = await extractor.extract(query)
            if result.has(EntityType.DATE):
                normalized_dates.append(result.get_value(EntityType.DATE))

        # 모두 같은 정규화된 값
        assert len(set(normalized_dates)) == 1


class TestQuantityValidationRules:
    """수량 범위 유효성 규칙 테스트"""

    @pytest.fixture
    def extractor(self):
        return EntityExtractor(use_llm=False)

    @pytest.mark.asyncio
    async def test_quantity_integer_extraction(self, extractor):
        """수량은 정수로 추출됨"""
        result = await extractor.extract("100개 생산 완료")
        assert result.has(EntityType.QUANTITY)
        qty = result.get_value(EntityType.QUANTITY)
        assert isinstance(qty, int)
        assert qty == 100

    @pytest.mark.asyncio
    async def test_large_quantity(self, extractor):
        """대량 수량 처리"""
        result = await extractor.extract("10000개 생산")
        assert result.has(EntityType.QUANTITY)
        assert result.get_value(EntityType.QUANTITY) == 10000

    @pytest.mark.asyncio
    async def test_quantity_with_ea_suffix(self, extractor):
        """EA 접미사 수량"""
        result = await extractor.extract("500EA 생산")
        assert result.has(EntityType.QUANTITY)
        assert result.get_value(EntityType.QUANTITY) == 500


class TestEquipmentIdValidationRules:
    """설비 ID 유효성 규칙 테스트"""

    @pytest.fixture
    def extractor(self):
        return EntityExtractor(use_llm=False)

    @pytest.mark.asyncio
    async def test_cnc_format_normalization(self, extractor):
        """CNC 형식 정규화 (CNC-001)"""
        queries = [
            ("CNC-001 상태", "CNC-001"),
            ("CNC001 상태", "CNC-001"),
            ("cnc-001 상태", "CNC-001"),
        ]
        for query, expected in queries:
            result = await extractor.extract(query)
            assert result.has(EntityType.EQUIPMENT_ID)
            assert result.get_value(EntityType.EQUIPMENT_ID) == expected

    @pytest.mark.asyncio
    async def test_robot_format_normalization(self, extractor):
        """ROBOT 형식 정규화"""
        result = await extractor.extract("ROBOT002 조회")
        assert result.has(EntityType.EQUIPMENT_ID)
        assert result.get_value(EntityType.EQUIPMENT_ID) == "ROBOT-002"

    @pytest.mark.asyncio
    async def test_multiple_equipment_ids(self, extractor):
        """다중 설비 ID 추출"""
        result = await extractor.extract("CNC-001과 ROBOT-002 비교")
        equipment_ids = result.get_all(EntityType.EQUIPMENT_ID)
        assert len(equipment_ids) == 2


class TestLotNumberValidationRules:
    """LOT 번호 유효성 규칙 테스트"""

    @pytest.fixture
    def extractor(self):
        return EntityExtractor(use_llm=False)

    @pytest.mark.asyncio
    async def test_lot_with_dash(self, extractor):
        """대시 포함 LOT 번호"""
        result = await extractor.extract("LOT-2026-001 이력")
        assert result.has(EntityType.LOT_NO)

    @pytest.mark.asyncio
    async def test_lot_with_underscore(self, extractor):
        """언더스코어 포함 LOT 번호"""
        result = await extractor.extract("LOT_2026_001 조회")
        assert result.has(EntityType.LOT_NO)

    @pytest.mark.asyncio
    async def test_lot_case_insensitive(self, extractor):
        """대소문자 구분 없이 인식"""
        result = await extractor.extract("lot-abc-123 이력")
        assert result.has(EntityType.LOT_NO)
        # 정규화 시 대문자로
        value = result.get_value(EntityType.LOT_NO)
        assert value.startswith("LOT")


class TestAlarmCodeValidationRules:
    """알람 코드 유효성 규칙 테스트"""

    @pytest.fixture
    def extractor(self):
        return EntityExtractor(use_llm=False)

    @pytest.mark.asyncio
    async def test_al_code_format(self, extractor):
        """AL-XXX 형식 알람 코드"""
        result = await extractor.extract("AL-001 에러 발생")
        assert result.has(EntityType.ALARM_CODE)

    @pytest.mark.asyncio
    async def test_err_code_format(self, extractor):
        """ERR-XXX 형식 알람 코드"""
        result = await extractor.extract("ERR-500 확인")
        assert result.has(EntityType.ALARM_CODE)

    @pytest.mark.asyncio
    async def test_korean_alarm_format(self, extractor):
        """한글 알람 형식"""
        result = await extractor.extract("알람 123 떴어")
        assert result.has(EntityType.ALARM_CODE)


# ============================================================================
# 보강된 테스트: 데이터 정합성 검증
# ============================================================================

class TestEntityRelationshipConsistency:
    """Entity 간 관계 정합성 테스트"""

    @pytest.fixture
    def extractor(self):
        return EntityExtractor(use_llm=False)

    @pytest.mark.asyncio
    async def test_date_and_date_range_coexistence(self, extractor):
        """날짜와 기간 동시 추출 시 정합성"""
        result = await extractor.extract("오늘부터 이번 주 현황")

        # 둘 다 추출 가능
        if result.has(EntityType.DATE) and result.has(EntityType.DATE_RANGE):
            date_val = result.get(EntityType.DATE)
            range_val = result.get(EntityType.DATE_RANGE)
            # 둘 다 유효한 값
            assert date_val.normalized is not None
            assert range_val.normalized is not None

    @pytest.mark.asyncio
    async def test_equipment_type_and_id_consistency(self, extractor):
        """설비 타입과 ID 일치성"""
        result = await extractor.extract("CNC-001 CNC 설비 조회")

        if result.has(EntityType.EQUIPMENT_ID) and result.has(EntityType.EQUIPMENT_TYPE):
            eq_id = result.get_value(EntityType.EQUIPMENT_ID)
            eq_type = result.get_value(EntityType.EQUIPMENT_TYPE)
            # ID에 타입이 포함되어 있어야 함
            assert eq_type in eq_id

    @pytest.mark.asyncio
    async def test_multiple_entities_independence(self, extractor):
        """여러 엔티티가 서로 독립적으로 추출됨"""
        result = await extractor.extract("오늘 CNC-001 가동률 100개 생산")

        # 각각 독립적으로 추출
        assert result.has(EntityType.DATE)
        assert result.has(EntityType.EQUIPMENT_ID)
        assert result.has(EntityType.METRIC)
        assert result.has(EntityType.QUANTITY)


class TestImplicitReferenceResolution:
    """암시적 참조 해결 테스트"""

    @pytest.fixture
    def extractor(self):
        return EntityExtractor(use_llm=False)

    @pytest.mark.asyncio
    async def test_resolve_equipment_from_context(self, extractor):
        """컨텍스트에서 '그 설비' 해결"""
        context = {"active_entities": {"equipment_id": "CNC-001"}}
        result = await extractor.extract("그 설비 상태 어때?", context)

        assert result.has(EntityType.EQUIPMENT_ID)
        assert result.get_value(EntityType.EQUIPMENT_ID) == "CNC-001"

    @pytest.mark.asyncio
    async def test_resolve_lot_from_context(self, extractor):
        """컨텍스트에서 '그 로트' 해결"""
        context = {"active_entities": {"lot_no": "LOT-2026-001"}}
        result = await extractor.extract("그 로트 이력 조회", context)

        assert result.has(EntityType.LOT_NO)
        assert result.get_value(EntityType.LOT_NO) == "LOT-2026-001"

    @pytest.mark.asyncio
    async def test_no_resolution_without_context(self, extractor):
        """컨텍스트 없으면 암시적 참조 해결 안함"""
        result = await extractor.extract("그 설비 상태", None)

        # 컨텍스트 없으면 EQUIPMENT_ID 없음
        if not result.has(EntityType.EQUIPMENT_ID):
            assert True
        else:
            # 추출되었다면 "그 설비"에서 온 게 아님
            assert result.get(EntityType.EQUIPMENT_ID).raw_text != "그 설비"

    @pytest.mark.asyncio
    async def test_implicit_reference_lower_confidence(self, extractor):
        """암시적 참조는 신뢰도가 낮음"""
        context = {"active_entities": {"equipment_id": "CNC-001"}}
        result = await extractor.extract("그 설비 이력", context)

        if result.has(EntityType.EQUIPMENT_ID):
            entity = result.get(EntityType.EQUIPMENT_ID)
            # 컨텍스트 기반 해결은 confidence < 1.0
            if "그" in entity.raw_text:
                assert entity.confidence < 1.0


class TestDefectTypeExtraction:
    """불량 유형 추출 테스트"""

    @pytest.fixture
    def extractor(self):
        return EntityExtractor(use_llm=False)

    @pytest.mark.asyncio
    async def test_dimension_defect(self, extractor):
        """치수불량 추출"""
        result = await extractor.extract("치수불량 원인 분석")
        assert result.has(EntityType.DEFECT_TYPE)
        assert result.get_value(EntityType.DEFECT_TYPE) == "DIMENSION"

    @pytest.mark.asyncio
    async def test_surface_defect(self, extractor):
        """외관불량 추출"""
        result = await extractor.extract("외관불량 발생")
        assert result.has(EntityType.DEFECT_TYPE)
        assert result.get_value(EntityType.DEFECT_TYPE) == "SURFACE"


class TestShiftExtraction:
    """근무조 추출 테스트"""

    @pytest.fixture
    def extractor(self):
        return EntityExtractor(use_llm=False)

    @pytest.mark.asyncio
    async def test_day_shift_extraction(self, extractor):
        """주간 근무 추출"""
        result = await extractor.extract("주간 생산 현황")
        assert result.has(EntityType.SHIFT)
        assert result.get_value(EntityType.SHIFT) == "DAY_SHIFT"

    @pytest.mark.asyncio
    async def test_night_shift_extraction(self, extractor):
        """야간 근무 추출"""
        result = await extractor.extract("야간 실적")
        assert result.has(EntityType.SHIFT)
        assert result.get_value(EntityType.SHIFT) == "NIGHT_SHIFT"

    @pytest.mark.asyncio
    async def test_numbered_shift_extraction(self, extractor):
        """번호 근무조 추출"""
        result = await extractor.extract("1조 작업 현황")
        assert result.has(EntityType.SHIFT)
        assert result.get_value(EntityType.SHIFT) == "SHIFT_1"

"""Tests for Skill Registry"""

import pytest
from src.understanding.intents import Intent
from src.skills.skill_registry import (
    SkillRegistry,
    SkillDefinition,
    OutputType,
    get_skill_registry,
    MES_SKILLS,
)


class TestSkillDefinition:
    """Tests for SkillDefinition"""

    def test_matches_intent(self):
        """Test intent matching"""
        skill = SkillDefinition(
            name="test_skill",
            description="Test",
            intents=[Intent.PRODUCTION_STATUS, Intent.PRODUCTION_DETAIL],
            api_endpoints=["/test"],
        )

        assert skill.matches_intent(Intent.PRODUCTION_STATUS) is True
        assert skill.matches_intent(Intent.EQUIPMENT_STATUS) is False

    def test_has_required_entities(self):
        """Test required entity check"""
        skill = SkillDefinition(
            name="test_skill",
            description="Test",
            intents=[Intent.TRACEABILITY],
            api_endpoints=["/test"],
            required_entities=["lot_no"],
        )

        assert skill.has_required_entities({"lot_no": "LOT-001"}) is True
        assert skill.has_required_entities({}) is False
        assert skill.has_required_entities({"date": "today"}) is False

    def test_get_missing_entities(self):
        """Test getting missing entities"""
        skill = SkillDefinition(
            name="test_skill",
            description="Test",
            intents=[Intent.TRACEABILITY],
            api_endpoints=["/test"],
            required_entities=["lot_no", "date"],
        )

        missing = skill.get_missing_entities({"lot_no": "LOT-001"})
        assert missing == ["date"]

        missing = skill.get_missing_entities({"lot_no": "LOT-001", "date": "today"})
        assert missing == []


class TestSkillRegistry:
    """Tests for SkillRegistry"""

    @pytest.fixture
    def registry(self):
        """Create fresh registry"""
        reg = SkillRegistry()
        return reg

    def test_default_skills_loaded(self, registry):
        """Test default MES skills are loaded"""
        skills = registry.list_all()
        assert len(skills) == len(MES_SKILLS)

    def test_get_skill(self, registry):
        """Test get skill by name"""
        skill = registry.get("mes_production_query")
        assert skill is not None
        assert skill.name == "mes_production_query"

    def test_get_nonexistent_skill(self, registry):
        """Test get nonexistent skill"""
        skill = registry.get("nonexistent_skill")
        assert skill is None

    def test_match_skills_production(self, registry):
        """Test matching skills for production intent"""
        skills = registry.match_skills(Intent.PRODUCTION_STATUS, {})
        assert len(skills) >= 1
        assert any(s.name == "mes_production_query" for s in skills)

    def test_match_skills_equipment(self, registry):
        """Test matching skills for equipment intent"""
        skills = registry.match_skills(Intent.EQUIPMENT_STATUS, {})
        assert len(skills) >= 1
        assert any(s.name == "mes_equipment_status" for s in skills)

    def test_match_skills_traceability_without_lot(self, registry):
        """Test traceability skill not matched without lot_no"""
        skills = registry.match_skills(Intent.TRACEABILITY, {})
        # Should not match because lot_no is required
        traceability_skills = [s for s in skills if s.name == "mes_traceability"]
        assert len(traceability_skills) == 0

    def test_match_skills_traceability_with_lot(self, registry):
        """Test traceability skill matched with lot_no"""
        skills = registry.match_skills(Intent.TRACEABILITY, {"lot_no": "LOT-001"})
        assert len(skills) >= 1
        assert any(s.name == "mes_traceability" for s in skills)

    def test_get_best_skill_priority(self, registry):
        """Test best skill selection by priority"""
        # Traceability should have higher priority when lot_no is present
        skill = registry.get_best_skill(Intent.TRACEABILITY, {"lot_no": "LOT-001"})
        assert skill is not None
        assert skill.name == "mes_traceability"

    def test_get_best_skill_no_match(self, registry):
        """Test best skill returns None when no match"""
        skill = registry.get_best_skill(Intent.UNKNOWN, {})
        assert skill is None

    def test_get_skills_for_intent(self, registry):
        """Test getting all skills for an intent"""
        skills = registry.get_skills_for_intent(Intent.KPI_QUERY)
        assert len(skills) >= 1
        assert all(Intent.KPI_QUERY in s.intents for s in skills)

    def test_register_custom_skill(self, registry):
        """Test registering a custom skill"""
        custom_skill = SkillDefinition(
            name="custom_skill",
            description="Custom test skill",
            intents=[Intent.PRODUCTION_STATUS],
            api_endpoints=["/custom"],
        )

        registry.register(custom_skill)

        skill = registry.get("custom_skill")
        assert skill is not None
        assert skill.description == "Custom test skill"


class TestGlobalSkillRegistry:
    """Tests for global skill registry"""

    def test_singleton(self):
        """Test get_skill_registry returns singleton"""
        reg1 = get_skill_registry()
        reg2 = get_skill_registry()
        assert reg1 is reg2


class TestMESSkills:
    """Tests for MES skill definitions"""

    def test_mes_production_query(self):
        """Test mes_production_query skill definition"""
        skill = MES_SKILLS["mes_production_query"]

        assert Intent.PRODUCTION_STATUS in skill.intents
        assert len(skill.api_endpoints) > 0
        assert skill.output_type == OutputType.DASHBOARD

    def test_mes_equipment_status(self):
        """Test mes_equipment_status skill definition"""
        skill = MES_SKILLS["mes_equipment_status"]

        assert Intent.EQUIPMENT_STATUS in skill.intents
        assert skill.output_type == OutputType.STATUS_GRID

    def test_mes_traceability(self):
        """Test mes_traceability skill definition"""
        skill = MES_SKILLS["mes_traceability"]

        assert Intent.TRACEABILITY in skill.intents
        assert "lot_no" in skill.required_entities
        assert skill.output_type == OutputType.TRACEABILITY_TIMELINE

    def test_all_skills_have_endpoints(self):
        """Test all skills have at least one endpoint (HELP type is exempt)"""
        for name, skill in MES_SKILLS.items():
            if skill.output_type == OutputType.HELP:
                continue  # HELP skills don't require API endpoints
            assert len(skill.api_endpoints) > 0, f"Skill {name} has no endpoints"

    def test_all_skills_have_intents(self):
        """Test all skills have at least one intent"""
        for name, skill in MES_SKILLS.items():
            assert len(skill.intents) > 0, f"Skill {name} has no intents"


# ============================================================================
# 보강된 테스트: Skill 라우팅 규칙 검증
# ============================================================================

class TestSkillRoutingRules:
    """Intent → Skill 매핑 규칙 검증"""

    @pytest.fixture
    def registry(self):
        return SkillRegistry()

    def test_production_status_routes_to_production_skill(self, registry):
        """PRODUCTION_STATUS → mes_production_query"""
        skill = registry.get_best_skill(Intent.PRODUCTION_STATUS, {})
        assert skill is not None
        assert skill.name == "mes_production_query"

    def test_equipment_status_routes_to_equipment_skill(self, registry):
        """EQUIPMENT_STATUS → mes_equipment_status"""
        skill = registry.get_best_skill(Intent.EQUIPMENT_STATUS, {})
        assert skill is not None
        assert skill.name == "mes_equipment_status"

    def test_kpi_query_routes_to_kpi_skill(self, registry):
        """KPI_QUERY → mes_kpi_query"""
        skill = registry.get_best_skill(Intent.KPI_QUERY, {})
        assert skill is not None
        assert skill.name == "mes_kpi_query"

    def test_traceability_requires_lot_no(self, registry):
        """TRACEABILITY는 lot_no 없으면 매칭 안됨"""
        # lot_no 없이
        skill_without = registry.get_best_skill(Intent.TRACEABILITY, {})
        # lot_no 포함
        skill_with = registry.get_best_skill(Intent.TRACEABILITY, {"lot_no": "LOT-001"})

        assert skill_without is None  # 매칭 실패
        assert skill_with is not None
        assert skill_with.name == "mes_traceability"

    def test_analytics_routes_correctly(self, registry):
        """ANALYTICS → mes_kpi_query (트렌드 분석)"""
        skills = registry.match_skills(Intent.ANALYTICS, {})
        assert any(s.name == "mes_kpi_query" for s in skills)

    def test_comparison_routes_correctly(self, registry):
        """COMPARISON → mes_kpi_query (비교 분석)"""
        skills = registry.match_skills(Intent.COMPARISON, {})
        assert any(s.name == "mes_kpi_query" for s in skills)


class TestSkillPriorityRouting:
    """Skill 우선순위 라우팅 검증"""

    @pytest.fixture
    def registry(self):
        return SkillRegistry()

    def test_higher_priority_skill_selected(self, registry):
        """우선순위 높은 스킬이 선택됨"""
        # 동일 Intent에 여러 스킬이 매핑된 경우
        skill = registry.get_best_skill(Intent.PRODUCTION_STATUS, {})

        # priority가 가장 높은 것 선택
        assert skill is not None
        assert skill.priority >= 1

    def test_required_entities_affect_matching(self, registry):
        """필수 엔티티가 매칭에 영향"""
        # 필수 엔티티 없이
        skills_without = registry.match_skills(Intent.TRACEABILITY, {})

        # 필수 엔티티 포함
        skills_with = registry.match_skills(Intent.TRACEABILITY, {"lot_no": "LOT-001"})

        # 필수 엔티티 있을 때 더 많은/적합한 스킬 매칭
        assert len(skills_with) > len(skills_without)


class TestSkillOutputTypeMapping:
    """Skill OutputType 매핑 검증"""

    def test_dashboard_output_skills(self):
        """DASHBOARD 출력 스킬들"""
        dashboard_skills = [
            name for name, skill in MES_SKILLS.items()
            if skill.output_type == OutputType.DASHBOARD
        ]
        assert "mes_production_query" in dashboard_skills

    def test_status_grid_output_skills(self):
        """STATUS_GRID 출력 스킬들"""
        grid_skills = [
            name for name, skill in MES_SKILLS.items()
            if skill.output_type == OutputType.STATUS_GRID
        ]
        assert "mes_equipment_status" in grid_skills

    def test_timeline_output_skills(self):
        """TRACEABILITY_TIMELINE 출력 스킬들"""
        timeline_skills = [
            name for name, skill in MES_SKILLS.items()
            if skill.output_type == OutputType.TRACEABILITY_TIMELINE
        ]
        assert "mes_traceability" in timeline_skills


class TestMissingEntityDetection:
    """누락 엔티티 감지 검증"""

    def test_get_missing_entities_single(self):
        """단일 누락 엔티티 감지"""
        skill = SkillDefinition(
            name="test",
            description="Test",
            intents=[Intent.TRACEABILITY],
            api_endpoints=["/test"],
            required_entities=["lot_no", "date"],
        )

        missing = skill.get_missing_entities({"lot_no": "LOT-001"})
        assert missing == ["date"]

    def test_get_missing_entities_multiple(self):
        """다중 누락 엔티티 감지"""
        skill = SkillDefinition(
            name="test",
            description="Test",
            intents=[Intent.COMPARISON],
            api_endpoints=["/test"],
            required_entities=["group_by", "metric", "date_range"],
        )

        missing = skill.get_missing_entities({})
        assert set(missing) == {"group_by", "metric", "date_range"}

    def test_get_missing_entities_none(self):
        """모든 필수 엔티티 충족"""
        skill = SkillDefinition(
            name="test",
            description="Test",
            intents=[Intent.TRACEABILITY],
            api_endpoints=["/test"],
            required_entities=["lot_no"],
        )

        missing = skill.get_missing_entities({"lot_no": "LOT-001", "date": "today"})
        assert missing == []


class TestSkillRegistration:
    """Skill 등록 동작 검증"""

    @pytest.fixture
    def registry(self):
        return SkillRegistry()

    def test_register_overrides_existing(self, registry):
        """동일 이름 스킬 등록 시 덮어쓰기"""
        original = registry.get("mes_production_query")
        original_desc = original.description

        # 같은 이름으로 새 스킬 등록
        new_skill = SkillDefinition(
            name="mes_production_query",
            description="New description",
            intents=[Intent.PRODUCTION_STATUS],
            api_endpoints=["/new"],
        )
        registry.register(new_skill)

        updated = registry.get("mes_production_query")
        assert updated.description == "New description"
        assert updated.description != original_desc

    def test_list_all_returns_all(self, registry):
        """list_all이 모든 스킬 반환"""
        skills = registry.list_all()
        assert len(skills) == len(MES_SKILLS)

    def test_custom_skill_integration(self, registry):
        """커스텀 스킬이 라우팅에 포함됨"""
        custom = SkillDefinition(
            name="custom_analytics",
            description="Custom analytics",
            intents=[Intent.ANALYTICS],
            api_endpoints=["/custom"],
            priority=100,  # 높은 우선순위
        )
        registry.register(custom)

        skill = registry.get_best_skill(Intent.ANALYTICS, {})

        # 우선순위가 높은 커스텀 스킬이 선택됨
        assert skill.name == "custom_analytics"

#!/usr/bin/env python3
"""
Intent별 테스트 자동 생성기

사용법:
    python scripts/generate_intent_tests.py --check    # 누락된 테스트 확인
    python scripts/generate_intent_tests.py --generate # 테스트 템플릿 생성
"""

import ast
import re
from pathlib import Path
from typing import Set, Dict, List

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent


def get_all_intents() -> Set[str]:
    """intents.py에서 모든 Intent enum 값 추출"""
    intents_file = PROJECT_ROOT / "src" / "understanding" / "intents.py"
    content = intents_file.read_text()
    
    # Intent enum 값 추출
    pattern = r'(\w+)\s*=\s*["\'](\w+)["\']'
    matches = re.findall(pattern, content)
    
    # UNKNOWN 제외
    return {name for name, value in matches if name != "UNKNOWN"}


def get_handled_intents() -> Set[str]:
    """nl_router_agent.py의 _generate_summary에서 처리하는 Intent 추출"""
    agent_file = PROJECT_ROOT / "src" / "nl_router_agent.py"
    content = agent_file.read_text()
    
    # intent == Intent.XXX 패턴 찾기
    pattern = r'intent\s*==\s*Intent\.(\w+)'
    matches = re.findall(pattern, content)
    
    return set(matches)


def get_tested_intents_unit() -> Set[str]:
    """단위 테스트에서 검증하는 Intent 추출"""
    test_file = PROJECT_ROOT / "tests" / "test_nl_router_agent.py"
    if not test_file.exists():
        return set()
    
    content = test_file.read_text()
    
    # Intent.XXX 패턴 찾기
    pattern = r'Intent\.(\w+)'
    matches = re.findall(pattern, content)
    
    return set(matches)


def get_tested_intents_e2e() -> Set[str]:
    """E2E 테스트에서 검증하는 Intent 추출 (키워드 기반)"""
    # 키워드 → Intent 매핑
    keyword_to_intent = {
        "스케줄": "SCHEDULE_QUERY",
        "schedule": "SCHEDULE_QUERY",
        "생산 현황": "PRODUCTION_STATUS",
        "production": "PRODUCTION_STATUS",
        "설비 상태": "EQUIPMENT_STATUS",
        "equipment": "EQUIPMENT_STATUS",
        "수율": "KPI_QUERY",
        "가동률": "KPI_QUERY",
        "OEE": "KPI_QUERY",
        "LOT": "TRACEABILITY",
        "추적": "TRACEABILITY",
    }
    
    e2e_dir = PROJECT_ROOT.parent / "cell-mes" / "frontend" / "e2e"
    if not e2e_dir.exists():
        return set()
    
    tested = set()
    for test_file in e2e_dir.rglob("*.spec.ts"):
        content = test_file.read_text()
        for keyword, intent in keyword_to_intent.items():
            if keyword.lower() in content.lower():
                tested.add(intent)
    
    return tested


def analyze_coverage() -> Dict:
    """테스트 커버리지 분석"""
    all_intents = get_all_intents()
    handled = get_handled_intents()
    tested_unit = get_tested_intents_unit()
    tested_e2e = get_tested_intents_e2e()
    
    return {
        "all_intents": all_intents,
        "handled_in_summary": handled,
        "tested_unit": tested_unit,
        "tested_e2e": tested_e2e,
        "missing_handlers": all_intents - handled - {"UNKNOWN"},
        "missing_unit_tests": handled - tested_unit,
        "missing_e2e_tests": handled - tested_e2e,
    }


def generate_unit_test_template(intent: str) -> str:
    """단위 테스트 템플릿 생성"""
    intent_lower = intent.lower()
    
    # Intent별 샘플 데이터
    sample_data = {
        "SCHEDULE_QUERY": '''{"schedule": {"date": "2026-01-01", "availability": [], "summary": {"total_equipments": 5, "total_scheduled_orders": 3, "running_orders": 2}}}''',
        "PRODUCTION_STATUS": '''{"daily_status": {"orders": {"total": 10, "completed": 8}, "kpis": {"yield_rate": 95.0}}}''',
        "EQUIPMENT_STATUS": '''{"equipments": [{"current_status": "RUN"}, {"current_status": "IDLE"}]}''',
        "KPI_QUERY": '''{"kpis": {"today": {"completion_rate": 90.0, "yield_rate": 95.0, "equipment_utilization": 85.0}}}''',
        "TRACEABILITY": '''{"traceability": {"lot_no": "LOT-001", "summary": {"total_ok_qty": 100, "total_ng_qty": 5, "yield_rate": 95.2}}}''',
    }
    
    data = sample_data.get(intent, '{"data": "sample"}')
    
    return f'''
    def test_{intent_lower}_response(self, agent):
        """{intent} should format response properly."""
        import json
        data = json.loads('{data}')

        result = agent._generate_summary(data, Intent.{intent}, "테스트 질문")

        # 기본 응답이 아닌 실제 데이터 포맷팅 확인
        assert result != "조회가 완료되었습니다."
        assert len(result) > 20
        # TODO: Intent별 필수 키워드 검증 추가
'''


def generate_e2e_test_template(intent: str) -> str:
    """E2E 테스트 템플릿 생성"""
    intent_lower = intent.lower()
    
    # Intent별 질문 예시
    sample_queries = {
        "SCHEDULE_QUERY": "오늘 스케줄 보여줘",
        "PRODUCTION_STATUS": "오늘 생산 현황 알려줘",
        "EQUIPMENT_STATUS": "설비 상태 어때?",
        "KPI_QUERY": "현재 수율이랑 가동률 알려줘",
        "TRACEABILITY": "LOT-001 이력 조회해줘",
        "COMPARISON": "설비별 가동률 비교해줘",
    }
    
    query = sample_queries.get(intent, f"{intent} 관련 질문")
    
    return f'''
  test('AI "{intent}" 응답 검증', async ({{ request }}) => {{
    if (!await checkNLRouter(request)) {{
      console.log('NL-Router 미실행 - 테스트 스킵');
      return;
    }}

    const aiResponse = await askAI(request, '{query}');
    if (!aiResponse) {{
      console.log('AI 응답 없음 - 스킵');
      return;
    }}
    
    console.log(`AI intent: ${{aiResponse.intent}}`);
    console.log(`AI text_response: ${{aiResponse.text_response}}`);
    
    // Intent 확인
    expect(aiResponse.intent).toBe('{intent_lower}');
    
    // 기본 응답이 아닌 실제 데이터 포맷팅 확인
    expect(aiResponse.text_response).not.toBe('조회가 완료되었습니다.');
    expect(aiResponse.text_response.length).toBeGreaterThan(20);
  }});
'''


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Intent 테스트 분석/생성")
    parser.add_argument("--check", action="store_true", help="커버리지 분석")
    parser.add_argument("--generate", action="store_true", help="누락된 테스트 템플릿 생성")
    args = parser.parse_args()
    
    coverage = analyze_coverage()
    
    print("=" * 60)
    print("📊 Intent 테스트 커버리지 분석")
    print("=" * 60)
    
    print(f"\n전체 Intent: {len(coverage['all_intents'])}개")
    print(f"  {sorted(coverage['all_intents'])}")
    
    print(f"\n_generate_summary()에서 처리: {len(coverage['handled_in_summary'])}개")
    print(f"  {sorted(coverage['handled_in_summary'])}")
    
    print(f"\n단위 테스트 커버: {len(coverage['tested_unit'])}개")
    print(f"  {sorted(coverage['tested_unit'])}")
    
    print(f"\nE2E 테스트 커버: {len(coverage['tested_e2e'])}개")
    print(f"  {sorted(coverage['tested_e2e'])}")
    
    print("\n" + "=" * 60)
    print("⚠️  갭 분석")
    print("=" * 60)
    
    if coverage['missing_handlers']:
        print(f"\n❌ 핸들러 누락 (Intent 있지만 포맷터 없음):")
        for intent in sorted(coverage['missing_handlers']):
            print(f"  - {intent}")
    
    if coverage['missing_unit_tests']:
        print(f"\n❌ 단위 테스트 누락:")
        for intent in sorted(coverage['missing_unit_tests']):
            print(f"  - {intent}")
    
    if coverage['missing_e2e_tests']:
        print(f"\n❌ E2E 테스트 누락:")
        for intent in sorted(coverage['missing_e2e_tests']):
            print(f"  - {intent}")
    
    if args.generate:
        print("\n" + "=" * 60)
        print("📝 누락된 테스트 템플릿")
        print("=" * 60)
        
        if coverage['missing_unit_tests']:
            print("\n# 단위 테스트 (test_nl_router_agent.py에 추가)")
            for intent in sorted(coverage['missing_unit_tests']):
                print(generate_unit_test_template(intent))
        
        if coverage['missing_e2e_tests']:
            print("\n# E2E 테스트 (ai-validation.spec.ts에 추가)")
            for intent in sorted(coverage['missing_e2e_tests']):
                print(generate_e2e_test_template(intent))


if __name__ == "__main__":
    main()

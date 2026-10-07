# `_legacy/` — 1회성 마이그레이션/검증 스크립트 보관

> **2026-05-02** Cross-platform collab readiness 정비 시 격리됨.

## 보관 스크립트

- `fix_imports.py` — 과거 import 경로 일괄 수정 스크립트 (1회성, 적용 완료)
- `refactor_cam.py` — CAM 모듈 리팩토링 도우미 (1회성, 적용 완료)
- `verify_product_flow.py` — 제품 흐름 검증 (개발 단계 진단용)

## 처리 정책

- **운영 코드 아님** — `src/` 와 격리하여 새 개발자가 prod 코드로 오인하지 않도록
- **삭제 보류** — git history에서 복구 가능하지만, 향후 비슷한 마이그레이션 시 참고 자료로 잠시 보존
- **다음 정리 시점** — `agents/digital-thread-project-manager`가 안정화되고 마이그레이션 패턴이 더 이상 필요 없을 때 git rm

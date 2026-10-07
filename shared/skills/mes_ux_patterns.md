# MES UX Patterns Guide

MES(Manufacturing Execution System) UI/UX 설계 시 현장 작업자 관점에서 고려해야 할 패턴들.

## 1. ID vs Code 처리

### 문제
- 내부적으로 auto-increment ID를 사용하지만, 사용자는 Code로 데이터를 인식
- ID 직접 입력 시 사용자 혼란 발생

### 해결 패턴
```typescript
// Bad: ID 직접 입력
<input type="number" value={productId} />

// Good: 드롭다운으로 Code/Name 표시, 내부적으로 ID 사용
<select value={productId} onChange={(e) => setProductId(parseInt(e.target.value))}>
  <option value="">선택하세요...</option>
  {products?.map((p) => (
    <option key={p.id} value={p.id}>
      {p.code} - {p.name}
    </option>
  ))}
</select>
```

### 규칙
- **입력**: 항상 드롭다운 또는 검색 자동완성 사용
- **표시**: ID 숨기고 Code/Name 표시, 필요시 tooltip에 ID 표시
- **목록**: 테이블에서 Code 컬럼 우선, ID는 숨기거나 축소

---

## 2. 마스터 데이터 연결 상태 표시

### 문제
- 제품에 라우팅이 없는데 작업지시 생성 가능 → 실행 시 오류
- 데이터 간 연결 상태가 사용자에게 보이지 않음

### 해결 패턴
```typescript
// 제품 목록에서 라우팅 유무 표시
{products.map((p) => (
  <tr>
    <td>{p.code}</td>
    <td>{p.name}</td>
    <td>
      {p.routing_count > 0 ? (
        <span className="badge badge-success">{p.routing_count}개 공정</span>
      ) : (
        <span className="badge badge-warning">라우팅 없음</span>
      )}
    </td>
  </tr>
))}

// 작업지시 생성 전 검증
const createOrder = async () => {
  const routings = await routingService.getByProduct(productId);
  if (routings.length === 0) {
    alert("선택한 제품에 라우팅이 설정되지 않았습니다. 먼저 라우팅을 설정해주세요.");
    return;
  }
  // 생성 진행...
};
```

### 규칙
- 연결이 필요한 데이터에 연결 상태 배지 표시
- 연결 없는 데이터에 경고 표시
- 작업 실행 전 필수 연결 검증

---

## 3. 비동기 작업 피드백

### 문제
- 스케줄 승인 후 작업지시 목록에 반영 안 됨 (느린 캐시 갱신)
- 작업 완료 후 다음 행동 불명확

### 해결 패턴
```typescript
const approveMutation = useMutation({
  mutationFn: approveSchedule,
  onSuccess: (data) => {
    // 1. 명확한 완료 메시지
    alert(`${data.updated_orders.length}개 작업지시가 업데이트되었습니다.`);

    // 2. 관련 캐시 즉시 무효화
    queryClient.invalidateQueries({ queryKey: ["orders"] });
    queryClient.invalidateQueries({ queryKey: ["scheduler-work-orders"] });

    // 3. 다음 행동 유도
    if (confirm("작업지시 목록을 확인하시겠습니까?")) {
      router.push("/production/orders");
    }
  },
});
```

### 규칙
- 작업 완료 시 구체적인 결과 표시 (N개 업데이트됨)
- 관련 데이터 캐시 즉시 무효화
- 다음 행동(페이지 이동, 새로고침 등) 옵션 제공

---

## 4. 에러 메시지 상세화

### 문제
- "Network Error" 또는 "400 Bad Request"만 표시
- 원인 파악 불가

### 해결 패턴
```typescript
onError: (error: any) => {
  let message = "작업 실패: ";

  if (error.code === "ERR_NETWORK") {
    message += "서버에 연결할 수 없습니다. 서버 상태를 확인해주세요.";
  } else if (error.response?.status === 400) {
    const detail = error.response.data?.detail;
    if (detail?.includes("Product not found")) {
      message += "선택한 제품이 존재하지 않습니다.";
    } else if (detail?.includes("duplicate") || detail?.includes("exists")) {
      message += "이미 존재하는 데이터입니다.";
    } else {
      message += detail || "입력 데이터를 확인해주세요.";
    }
  } else if (error.response?.status === 401) {
    message += "로그인이 필요합니다.";
  } else if (error.response?.status === 422) {
    message += "필수 항목이 누락되었습니다.";
  } else {
    message += error.message || "알 수 없는 오류가 발생했습니다.";
  }

  alert(message);
}
```

### 에러 메시지 가이드

| HTTP 상태 | 상황 | 사용자 메시지 |
|-----------|------|---------------|
| Network Error | 서버 미응답 | "서버에 연결할 수 없습니다" |
| 400 duplicate | 중복 데이터 | "이미 존재하는 XXX입니다" |
| 400 not found | FK 참조 오류 | "선택한 XXX이 존재하지 않습니다" |
| 401 | 인증 필요 | "로그인이 필요합니다" |
| 403 | 권한 없음 | "이 작업에 대한 권한이 없습니다" |
| 422 | 유효성 검사 실패 | "필수 항목을 확인해주세요" |
| 500 | 서버 오류 | "서버 오류가 발생했습니다" |

---

## 5. 외부 서비스 연동 상태 표시

### 문제
- 미들웨어/스케줄러 연결 상태 확인 불가
- 동기화 실패 원인 불명확

### 해결 패턴
```typescript
// 헬스체크 쿼리
const { data: middlewareHealth } = useQuery({
  queryKey: ["middleware-health"],
  queryFn: () => equipmentService.checkMiddlewareHealth(),
  refetchInterval: 30000, // 30초마다 확인
  retry: false,
});

// 상태 배지 표시
<div className="flex items-center gap-2">
  {middlewareHealth?.status === "connected" ? (
    <span className="flex items-center gap-1 text-green-600">
      <Wifi size={14} /> 연결됨
    </span>
  ) : (
    <span className="flex items-center gap-1 text-red-600">
      <WifiOff size={14} /> 연결 안됨
    </span>
  )}
  <span className="text-xs text-gray-400">{middlewareHealth?.url}</span>
</div>

// 연결 안됨 시 동기화 버튼 비활성화
<button
  onClick={sync}
  disabled={middlewareHealth?.status !== "connected"}
  title={middlewareHealth?.status !== "connected" ? "미들웨어 연결 필요" : ""}
>
  동기화
</button>
```

---

## 6. 자동 로드 및 상태 관리

### 문제
- 제품 선택 후 "라우팅 불러오기" 수동 클릭 필요
- 제품 변경 시 이전 데이터 잔존

### 해결 패턴
```typescript
// 자동 로드
useEffect(() => {
  if (existingRoutings && selectedProduct) {
    setRoutings(existingRoutings.map(transformRouting));
    setHasUnsavedChanges(false);
  } else if (selectedProduct) {
    setRoutings([]); // 새 제품이면 빈 상태
  }
}, [existingRoutings, selectedProduct]);

// 변경사항 추적
const updateWithChange = (newData) => {
  setData(newData);
  setHasUnsavedChanges(true);
};

// 전환 시 경고
const handleProductSelect = (product) => {
  if (hasUnsavedChanges) {
    if (!confirm("저장되지 않은 변경사항이 있습니다. 계속하시겠습니까?")) {
      return;
    }
  }
  setSelectedProduct(product);
};

// 상태 표시
{hasUnsavedChanges && (
  <span className="badge badge-warning">변경사항 있음</span>
)}
```

---

## 7. 데이터 입력 워크플로우

### 표준 순서
```
1. 표준공정 등록
   ↓
2. 제품 등록
   ↓
3. 라우팅 설계 (제품 → 표준공정 연결)
   ↓
4. 시나리오 등록 (선택사항)
   ↓
5. 작업지시 생성 (제품 + 시나리오 선택)
   ↓
6. 스케줄링 (계획 수립)
   ↓
7. 생산 실행 (상태 전이: READY → RUNNING → DONE)
```

### 검증 포인트
- 제품 등록 시: 코드 중복 검사
- 라우팅 설계 시: 최소 1개 공정 필요
- 작업지시 생성 시: 제품 라우팅 존재 검사
- 스케줄링 실행 시: 가용 설비 존재 검사

---

## 8. 시드 데이터 무결성

### 검증 항목
```python
async def validate_seed_data(session):
    issues = {"errors": [], "warnings": []}

    # 1. 라우팅 없는 제품
    # 2. 존재하지 않는 제품 참조하는 작업지시
    # 3. 존재하지 않는 표준공정 참조하는 라우팅
    # 4. 중복 lot_no
    # 5. 중복 제품 코드
    # 6. 중복 표준공정 코드

    return issues
```

### 사용법
```bash
# 시드 데이터 생성 후 자동 검증
uv run python -m src.seed_data

# 검증만 실행
uv run python -m src.seed_data --validate
```

---

## 9. 체크리스트

### 새 기능 개발 시
- [ ] ID 대신 Code/Name 표시하는가?
- [ ] 연결 데이터 상태 표시하는가?
- [ ] 에러 메시지가 사용자 친화적인가?
- [ ] 비동기 작업 후 캐시 무효화하는가?
- [ ] 외부 서비스 연결 상태 표시하는가?
- [ ] 자동 로드 구현되어 있는가?
- [ ] 미저장 변경사항 경고하는가?

### 코드 리뷰 시
- [ ] 사용자 입력 검증이 프론트엔드와 백엔드 모두에 있는가?
- [ ] FK 참조 전 존재 검사하는가?
- [ ] 상태 전이 규칙 검증하는가?

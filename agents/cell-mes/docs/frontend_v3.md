# [MES] 프론트엔드 설계 명세서 (v3.0)

## 1. 개요 (Overview)
* **Version:** 3.0
* **Framework:** **Next.js 14+ (App Router)**
* **Deployment:** **Windows Native (Standalone)**
* **Base Schema:** Database Schema v3.0 (AAS & JSONB 반영)
* **Project Goal:** 표준 공정 기반의 정밀 제어와 AAS 기반의 유연한 장비 연동(Plug & Play)을 지원하는 모던 웹 시스템 구축.

## 2. 기술 스택 (Tech Stack)
* **Core:** Next.js (App Router), TypeScript
* **Runtime:** Node.js (LTS Version - Windows 설치 필요)
* **API Client:** **Axios** (Interceptors를 통한 토큰 관리)
* **State Management:**
    * **Server:** TanStack Query (데이터 캐싱, 폴링, Optimistic Update)
    * **Client:** Zustand (전역 UI 상태)
* **Styling:** Tailwind CSS, Shadcn/UI
* **Visualization:**
    * **Chart:** Recharts (실시간 대시보드)
    * **Flow:** ReactFlow (공정 라우팅 시각화 - Drag & Drop)
    * **JSON:** `react-json-view` (**[New]** 설비 스펙 및 실시간 데이터 뷰어)
* **Process Manager:** PM2 (Windows 서비스 등록용)

---

## 3. 폴더 구조 (Project Structure)
API 서비스(`services/`) 폴더를 모듈별로 상세화했습니다.

```text
app/
├── (auth)/                  # [Layout: No Sidebar]
│   ├── login/page.tsx
│   └── register/page.tsx
├── (main)/                  # [Layout: Sidebar + Header]
│   ├── layout.tsx
│   ├── page.tsx             # 대시보드
│   ├── master/              # 기준 정보
│   │   ├── processes/       # 표준 공정
│   │   ├── products/        # 품목 관리
│   │   ├── routings/        # 공정 라우팅
│   │   ├── scenarios/       # 물류 시나리오
│   │   └── equipments/      # 설비 관리 [v3]
│   ├── production/          # 생산 관리
│   │   ├── orders/          # 작업 지시
│   │   └── results/         # 생산 실적
│   └── system/              # 시스템 설정
│       ├── users/           # 사용자 관리
│       └── middleware/      # 미들웨어 설정
├── lib/                     # 공통 유틸리티
│   └── axios.ts             # [중요] Axios Instance (Auth Header 설정)
├── services/                # [API Service Layer] - 백엔드 통신 모듈
│   ├── auth.ts              # 로그인, 회원가입
│   ├── user.ts              # 사용자 관리
│   ├── system.ts            # 미들웨어 설정
│   ├── master/              # 기준 정보 관련 서비스
│   │   ├── product.ts
│   │   ├── process.ts
│   │   ├── routing.ts       # 라우팅 & 파일 저장
│   │   ├── scenario.ts
│   │   └── equipment.ts     # AAS Sync & Polling [v3]
│   └── production/          # 생산 관련 서비스
│       ├── order.ts         # 작업 지시 제어
│       └── result.ts        # 실적 조회
└── types/                   # TypeScript Type Definitions

```

---

## 4. 핵심 기능 상세 명세 (Feature Specifications)

### A. 인증 (Authentication)

* **Login (`/login`):** JWT 토큰 발급. `lib/axios.ts`에서 Authorization 헤더 자동 주입.
* **Register (`/register`):** 관리자/작업자 권한(Role) 선택 가입.

### B. 대시보드 (Dashboard)

* **경로:** `/`
* **Logic:** `equipment.ts/fetchEquipments`를 3초마다 폴링(Polling)하여 KPI 및 가동 상태 카드 갱신.

### C. 기준 정보 관리 (Master Data)

#### 1. 공정 라우팅 (`/master/routings`)

* **기능:** 품목별 공정 순서 정의 및 **NC 파일 매핑**.
* **API 호출:**
* 조회: `product.ts/fetchProductRoutings(id)`
* 저장: `routing.ts/saveRoutings(id, data)` (ReactFlow 노드 데이터를 DTO로 변환하여 전송).


* **Interaction:** 노드 클릭 시 파일 업로드 팝업 호출.

#### 2. 설비 관리 (`/master/equipments`) - **[v3]**

* **기능:** AAS 동기화 및 JSON 데이터 조회.
* **API 호출:**
* 동기화: `equipment.ts/syncEquipments()` 호출 시 로딩 스피너 표시.
* 상세 조회: `equipment.ts/fetchEquipmentDetail(id)` 호출 결과를 `react-json-view`로 렌더링.



### D. 생산 관리 (Production)

#### 1. 작업 지시 (`/production/orders`)

* **기능:** 지시 생성 및 제어.
* **API 호출:**
* 생성: `order.ts/createOrder(payload)` (품목 ID, 시나리오 ID 포함).
* 제어: `order.ts/updateOrderStatus(id, status)` (START/STOP).



---

## 5. API 연동 인터페이스 (Service Layer Detail)

개발 시 바로 사용할 수 있도록 **모든 API 호출 함수**를 정의했습니다.

### 5.0. 공통 설정 (`lib/axios.ts`)

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  timeout: 5000,
});

// Request Interceptor: 토큰 자동 주입
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default api;

```

### 5.1. 인증 및 사용자 서비스 (`services/auth.ts`, `user.ts`)

```typescript
// auth.ts
export const login = (credentials: LoginDto) => api.post('/auth/login', credentials);
export const register = (data: RegisterDto) => api.post('/users', data);

// user.ts
export const fetchUsers = () => api.get('/users');
export const updateUserRole = (id: number, role: string) => api.patch(`/users/${id}/role`, { role });

```

### 5.2. 기준 정보 서비스 (`services/master/*.ts`)

```typescript
// services/master/product.ts
export const fetchProducts = () => api.get('/masters/products');
export const createProduct = (data: ProductDto) => api.post('/masters/products', data);

// services/master/process.ts
export const fetchProcesses = () => api.get('/masters/processes');
export const createProcess = (data: ProcessDto) => api.post('/masters/processes', data);

// services/master/routing.ts [핵심]
export const fetchRoutings = (productId: number) => api.get(`/masters/products/${productId}/routings`);
export const saveRoutings = (productId: number, routings: RoutingDto[]) => 
  api.put(`/masters/products/${productId}/routings`, routings);

// services/master/scenario.ts
export const fetchScenarios = () => api.get('/masters/scenarios');
export const createScenario = (data: ScenarioDto) => api.post('/masters/scenarios', data);

// services/master/equipment.ts [v3 AAS]
export const fetchEquipments = () => api.get('/masters/equipments');
export const syncEquipments = () => api.post('/masters/equipments/sync'); // Asset Discovery
export const fetchEquipmentStatus = (id: number) => api.get(`/masters/equipments/${id}/status`);

```

### 5.3. 생산 관리 서비스 (`services/production/*.ts`)

```typescript
// services/production/order.ts
export const fetchOrders = () => api.get('/production/orders');
export const createOrder = (data: OrderDto) => api.post('/production/orders', data);
export const updateOrderStatus = (id: number, status: string) => 
  api.patch(`/production/orders/${id}/status`, { status });

// services/production/result.ts
export const fetchResults = () => api.get('/production/results');
export const fetchTraceability = (lotNo: string) => api.get(`/production/results/${lotNo}/trace`);

```

### 5.4. 시스템 설정 서비스 (`services/system.ts`)

```typescript
export const fetchMiddleware = () => api.get('/system/middleware');
export const createMiddleware = (data: MiddlewareDto) => api.post('/system/middleware', data);
export const testConnection = (id: number) => api.post(`/system/middleware/${id}/test`);

```

---

## 6. 윈도우 배포 가이드 (Deployment)

1. **빌드 설정 (`next.config.js`):**
```javascript
module.exports = { output: 'standalone' }

```


2. **환경 변수 (`.env.production`):**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

```


3. **실행:**
* 빌드된 `.next/standalone` 폴더를 윈도우 서버로 이동.
* `node server.js` 실행 (또는 PM2 사용).


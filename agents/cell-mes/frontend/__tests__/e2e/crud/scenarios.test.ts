import { describe, it, expect, afterAll } from 'vitest'
import { commands } from 'vitest/browser'

const APP_URL = 'http://localhost:3000'

async function login() {
  await commands.goto(`${APP_URL}/login`)
  await commands.fillByRole('textbox', '사용자 ID', 'admin')
  await commands.fillByLabel('비밀번호', 'admin123')
  await commands.clickByRole('button', '로그인')
  await commands.waitForUrl('^(?!.*\\/login)', 10_000)
}

afterAll(async () => {
  await commands.closeAppPage()
})

describe('물류 시나리오 CRUD 테스트', () => {
  describe('Read: 목록 조회', () => {
    it('페이지 제목 표시', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/scenarios`)
      await commands.waitForTimeout(2000)

      const hasHeading = await commands.isVisibleByText('물류 시나리오', 5_000)
      expect(hasHeading).toBe(true)
    })

    it('설명 텍스트 표시', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/scenarios`)
      await commands.waitForTimeout(2000)

      const hasDesc = await commands.isVisibleByText('AGV.*로봇.*시나리오', 5_000)
      expect(hasDesc).toBe(true)
    })

    it('테이블 또는 빈 상태 표시', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/scenarios`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      const hasEmpty = await commands.isVisibleByText('등록된 시나리오가 없습니다', 3_000)
      expect(hasTable || hasEmpty).toBe(true)
    })

    it('테이블 헤더 확인 (데이터 있는 경우)', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/scenarios`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      if (hasTable) {
        const headers = ['코드', '시나리오명', '대상 제품', '제어 파일', '상태', '등록일', '액션']
        for (const header of headers) {
          const hasHeader = await commands.isVisibleByText(header, 3_000)
          expect(hasHeader).toBe(true)
        }
      }
    })

    it('"시나리오 추가" 버튼 표시', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/scenarios`)
      await commands.waitForTimeout(2000)

      const hasAddBtn = await commands.isVisibleByText('시나리오 추가', 5_000)
      expect(hasAddBtn).toBe(true)
    })
  })

  describe('Read: API 검증', () => {
    it('GET /scenarios 유효한 응답 반환', async () => {
      const result = await commands.fetchApi('/masters/scenarios')
      expect(result.ok).toBe(true)
      expect(result.status).toBe(200)
      expect(Array.isArray(result.data)).toBe(true)
    })

    it('시나리오 항목에 필수 필드 포함', async () => {
      const result = await commands.fetchApi('/masters/scenarios')
      expect(result.ok).toBe(true)

      if (result.data.length > 0) {
        const scenario = result.data[0]
        expect(scenario).toHaveProperty('id')
        expect(scenario).toHaveProperty('name')
        expect(scenario).toHaveProperty('file_path')
        expect(scenario).toHaveProperty('is_active')
      }
    })
  })

  describe('Create: 시나리오 추가 모달', () => {
    it('시나리오 추가 모달 열기 및 폼 필드 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/scenarios`)
      await commands.waitForTimeout(2000)

      await commands.clickByText('시나리오 추가')
      await commands.waitForTimeout(1000)

      // 모달 확인
      const hasModal = await commands.isVisibleBySelector('.fixed.inset-0', 5_000)
      expect(hasModal).toBe(true)

      // 폼 라벨 확인
      const labels = ['시나리오 코드', '시나리오명', '제어 파일 경로', '대상 제품']
      for (const label of labels) {
        const hasLabel = await commands.isVisibleByText(label, 3_000)
        expect(hasLabel).toBe(true)
      }

      // 입력 필드 확인
      const hasInputs = await commands.isVisibleBySelector('input', 3_000)
      expect(hasInputs).toBe(true)

      // 제품 선택 드롭다운
      const hasSelect = await commands.isVisibleBySelector('select', 3_000)
      expect(hasSelect).toBe(true)

      // 저장/취소 버튼
      const hasSave = await commands.isVisibleByRole('button', '저장')
      expect(hasSave).toBe(true)

      const hasCancel = await commands.isVisibleByRole('button', '취소')
      expect(hasCancel).toBe(true)

      // 코드 자동 생성 안내 텍스트
      const hasAutoGenText = await commands.isVisibleByText('비워두면 자동 생성', 3_000)
      expect(hasAutoGenText).toBe(true)

      // 취소
      await commands.clickByRole('button', '취소')
      await commands.waitForTimeout(500)
    })

    it('필수 필드 비어있으면 제출 방지', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/scenarios`)
      await commands.waitForTimeout(2000)

      await commands.clickByText('시나리오 추가')
      await commands.waitForTimeout(500)

      // 빈 폼으로 제출 시도
      await commands.clickByRole('button', '저장')
      await commands.waitForTimeout(500)

      // HTML5 validation으로 모달이 열려있어야 함
      const hasModal = await commands.isVisibleBySelector('.fixed.inset-0', 3_000)
      expect(hasModal).toBe(true)

      await commands.clickByRole('button', '취소')
      await commands.waitForTimeout(500)
    })
  })

  describe('Create & Delete: API를 통한 전체 CRUD 흐름', () => {
    it('시나리오 생성 -> 확인 -> 삭제', async () => {
      const scenarioName = `VT_Scenario_${Date.now()}`
      const filePath = `/scenarios/test_${Date.now()}.yaml`

      // 생성 (code 필수 필드 포함)
      const scenarioCode = `VT-${Date.now().toString(36).slice(-6).toUpperCase()}`
      const createResult = await commands.fetchApi(
        '/masters/scenarios',
        'POST',
        JSON.stringify({
          code: scenarioCode,
          name: scenarioName,
          file_path: filePath,
          is_active: true,
        })
      )
      expect(createResult.ok).toBe(true)
      expect(createResult.data).toHaveProperty('id')
      const createdId = createResult.data.id

      // API 목록에서 확인 (active_only=false로 전체 조회)
      const listResult = await commands.fetchApi('/masters/scenarios?active_only=false')
      expect(listResult.ok).toBe(true)
      const found = listResult.data.find((s: any) => s.name === scenarioName)
      expect(found).toBeDefined()
      expect(found.file_path).toBe(filePath)
      expect(found.is_active).toBe(true)

      // UI에서 확인
      await login()
      await commands.goto(`${APP_URL}/master/scenarios`)
      await commands.waitForTimeout(2000)

      const hasName = await commands.isVisibleByText(scenarioName, 5_000)
      expect(hasName).toBe(true)

      // 삭제
      const deleteResult = await commands.fetchApi(`/masters/scenarios/${createdId}`, 'DELETE')
      expect(deleteResult.ok).toBe(true)

      // 삭제 확인
      const afterDelete = await commands.fetchApi('/masters/scenarios')
      const notFound = afterDelete.data.find((s: any) => s.name === scenarioName)
      expect(notFound).toBeUndefined()
    })
  })

  describe('Update: 시나리오 활성 상태 전환', () => {
    it('시나리오 활성/비활성 전환 via API (PATCH /active)', async () => {
      // 생성 (code 필수 필드 포함)
      const updCode = `VTU-${Date.now().toString(36).slice(-6).toUpperCase()}`
      const createResult = await commands.fetchApi(
        '/masters/scenarios',
        'POST',
        JSON.stringify({
          code: updCode,
          name: `VT_UPD_${Date.now()}`,
          file_path: `/scenarios/update_test.yaml`,
          is_active: true,
        })
      )
      expect(createResult.ok).toBe(true)
      const id = createResult.data.id

      // 비활성화 (PATCH /{id}/active?is_active=false)
      const deactivateResult = await commands.fetchApi(
        `/masters/scenarios/${id}/active?is_active=false`,
        'PATCH'
      )
      expect(deactivateResult.ok).toBe(true)
      expect(deactivateResult.data.is_active).toBe(false)

      // 재활성화
      const activateResult = await commands.fetchApi(
        `/masters/scenarios/${id}/active?is_active=true`,
        'PATCH'
      )
      expect(activateResult.ok).toBe(true)
      expect(activateResult.data.is_active).toBe(true)

      // 정리
      await commands.fetchApi(`/masters/scenarios/${id}`, 'DELETE')
    })
  })

  describe('Toggle: 활성/비활성 전환', () => {
    it('활성 상태 토글 확인 (UI)', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/scenarios`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      if (hasTable) {
        // 활성 또는 비활성 상태 버튼이 보여야 함
        const hasActive = await commands.isVisibleByText('활성', 3_000)
        const hasInactive = await commands.isVisibleByText('비활성', 3_000)
        expect(hasActive || hasInactive).toBe(true)
      }
    })
  })
})

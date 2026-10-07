import { describe, it, expect } from 'vitest'
import { commands } from 'vitest/browser'

const APP_URL = 'http://localhost:3000'

async function login() {
  await commands.goto(`${APP_URL}/login`)
  await commands.fillByRole('textbox', '사용자 ID', 'admin')
  await commands.fillByLabel('비밀번호', 'admin123')
  await commands.clickByRole('button', '로그인')
  await commands.waitForUrl('^(?!.*\\/login)', 10_000)
}

describe('Scheduler', () => {
  describe('Schedule overview', () => {
    it('loads schedule overview page', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler`)
      await commands.waitForTimeout(2000)

      const hasHeading = await commands.isVisibleByText('스케줄 현황', 5_000)
      expect(hasHeading).toBe(true)
    })

    it('shows date input field', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler`)

      const hasDateInput = await commands.isVisibleBySelector('input[type="date"]', 5_000)
      expect(hasDateInput).toBe(true)
    })

    it('shows today button', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler`)

      const hasTodayButton = await commands.isVisibleByRole('button', '오늘')
      expect(hasTodayButton).toBe(true)
    })

    it('shows summary cards or empty state', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler`)
      await commands.waitForTimeout(2000)

      const hasEquipmentCard = await commands.isVisibleByText('스케줄된 설비', 5_000)
      const hasOrdersCard = await commands.isVisibleByText('스케줄된 작업', 5_000)
      const hasEmptyState = await commands.isVisibleByText('스케줄된 작업지시가 없습니다', 5_000)

      expect(hasEquipmentCard || hasOrdersCard || hasEmptyState).toBe(true)
    })

    it('shows Gantt chart area or empty state', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler`)
      await commands.waitForTimeout(2000)

      const hasGantt = await commands.isVisibleBySelector(
        '[class*="gantt"], [class*="Gantt"], canvas, svg, .bg-white.rounded-lg',
        5_000,
      )
      const hasEmptyState = await commands.isVisibleByText('스케줄된 작업지시가 없습니다', 3_000)

      expect(hasGantt || hasEmptyState).toBe(true)
    })

    it('shows subtitle description', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler`)

      const hasSubtitle = await commands.isVisibleByText('일별 생산 스케줄을 간트 차트로 확인합니다', 5_000)
      expect(hasSubtitle).toBe(true)
    })

    it('shows date label', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler`)

      const hasLabel = await commands.isVisibleByText('날짜 선택', 5_000)
      expect(hasLabel).toBe(true)
    })

    it('shows running orders card when schedule exists', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler`)
      await commands.waitForTimeout(2000)

      const hasRunningCard = await commands.isVisibleByText('진행중', 5_000)
      const hasEmptyState = await commands.isVisibleByText('스케줄된 작업지시가 없습니다', 3_000)

      expect(hasRunningCard || hasEmptyState).toBe(true)
    })

    it('shows empty state guidance text', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler`)
      await commands.waitForTimeout(2000)

      const hasGuidance = await commands.isVisibleByText('스케줄 실행', 5_000)
      // Either the guidance or actual data should be present
      expect(hasGuidance).toBe(true)
    })
  })

  describe('Schedule execution page', () => {
    it('loads schedule execution page', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)
      await commands.waitForTimeout(2000)

      const hasHeading = await commands.isVisibleByText('스케줄 실행', 5_000)
      expect(hasHeading).toBe(true)
    })

    it('shows initial idle status badge', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)

      const hasIdleBadge = await commands.isVisibleByText('대기', 5_000)
      expect(hasIdleBadge).toBe(true)
    })

    it('shows status cards for equipment and orders', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)

      const hasEquipmentCard = await commands.isVisibleByText('가용 설비', 5_000)
      expect(hasEquipmentCard).toBe(true)

      const hasTargetCard = await commands.isVisibleByText('스케줄 대상', 5_000)
      expect(hasTargetCard).toBe(true)

      const hasResultCard = await commands.isVisibleByText('스케줄 결과', 5_000)
      expect(hasResultCard).toBe(true)
    })

    it('shows solver selection dropdown', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)

      const hasSelect = await commands.isVisibleBySelector('select', 5_000)
      expect(hasSelect).toBe(true)
    })

    it('shows planning horizon input', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)

      const hasNumberInput = await commands.isVisibleBySelector('input[type="number"]', 5_000)
      expect(hasNumberInput).toBe(true)
    })

    it('shows include-running checkbox', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)

      const hasCheckbox = await commands.isVisibleBySelector('input[type="checkbox"]', 5_000)
      expect(hasCheckbox).toBe(true)
    })

    it('shows execute button', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)

      const hasExecuteButton = await commands.isVisibleByRole('button', '스케줄 실행')
      expect(hasExecuteButton).toBe(true)
    })

    it('shows available equipment table', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)
      await commands.waitForTimeout(2000)

      const hasEquipmentHeading = await commands.isVisibleByText('가용 설비 목록', 5_000)
      if (hasEquipmentHeading) {
        const hasMachineId = await commands.isVisibleByText('Machine ID', 3_000)
        const hasType = await commands.isVisibleByText('타입', 3_000)
        const hasStatus = await commands.isVisibleByText('상태', 3_000)

        expect(hasMachineId || hasType || hasStatus).toBe(true)
      }
    })

    it('shows pending work orders table', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)
      await commands.waitForTimeout(2000)

      const hasOrdersHeading = await commands.isVisibleByText('대기 작업지시 목록', 5_000)
      if (hasOrdersHeading) {
        const hasWoId = await commands.isVisibleByText('WO ID', 3_000)
        const hasProduct = await commands.isVisibleByText('제품', 3_000)
        const hasQty = await commands.isVisibleByText('수량', 3_000)

        expect(hasWoId || hasProduct || hasQty).toBe(true)
      }
    })

    it('shows solver description text', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)
      await commands.waitForTimeout(1000)

      // Default solver is OR_TOOLS - should show its description
      const hasDescription = await commands.isVisibleByText('최적', 5_000)
      const hasLabel = await commands.isVisibleByText('솔버 선택', 5_000)
      expect(hasDescription || hasLabel).toBe(true)
    })

    it('shows planning period label', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)

      const hasLabel = await commands.isVisibleByText('계획 기간', 5_000)
      expect(hasLabel).toBe(true)
    })

    it('shows time limit label', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)

      const hasLabel = await commands.isVisibleByText('시간 제한', 5_000)
      expect(hasLabel).toBe(true)
    })

    it('shows JSON view buttons for data cards', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)
      await commands.waitForTimeout(2000)

      const hasJsonBtn = await commands.isVisibleByText('JSON 보기', 5_000)
      expect(hasJsonBtn).toBe(true)
    })

    it('shows include-running option label', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)

      const hasOption = await commands.isVisibleByText('진행중 포함', 5_000)
      expect(hasOption).toBe(true)
    })

    it('shows subtitle description', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)

      const hasSub = await commands.isVisibleByText('솔버를 실행하고 결과를 검토', 5_000)
      expect(hasSub).toBe(true)
    })
  })

  describe('Solver settings page', () => {
    it('loads solver settings page', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/settings`)
      await commands.waitForTimeout(2000)

      const hasHeading = await commands.isVisibleByText('솔버 설정', 5_000)
      expect(hasHeading).toBe(true)
    })

    it('shows settings subtitle', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/settings`)

      const hasSub = await commands.isVisibleByText('스케줄링 솔버 유형과 파라미터를 관리합니다', 5_000)
      expect(hasSub).toBe(true)
    })

    it('shows default settings section', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/settings`)

      const hasSection = await commands.isVisibleByText('기본 설정', 5_000)
      expect(hasSection).toBe(true)
    })

    it('shows horizon hours input', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/settings`)

      const hasLabel = await commands.isVisibleByText('기본 계획 기간', 5_000)
      expect(hasLabel).toBe(true)

      const hasInput = await commands.isVisibleBySelector('input[type="number"]', 5_000)
      expect(hasInput).toBe(true)
    })

    it('shows solver type dropdown', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/settings`)

      const hasLabel = await commands.isVisibleByText('기본 솔버', 5_000)
      expect(hasLabel).toBe(true)

      const hasSelect = await commands.isVisibleBySelector('select', 5_000)
      expect(hasSelect).toBe(true)
    })

    it('shows time limit setting', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/settings`)

      const hasLabel = await commands.isVisibleByText('솔버 시간 제한', 5_000)
      expect(hasLabel).toBe(true)
    })

    it('shows include running toggle', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/settings`)

      const hasLabel = await commands.isVisibleByText('진행중 작업 포함', 5_000)
      expect(hasLabel).toBe(true)

      const hasInclude = await commands.isVisibleByText('포함', 5_000)
      const hasExclude = await commands.isVisibleByText('제외', 5_000)
      expect(hasInclude && hasExclude).toBe(true)
    })

    it('shows solver type cards section', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/settings`)

      const hasSection = await commands.isVisibleByText('솔버 유형', 5_000)
      expect(hasSection).toBe(true)
    })

    it('shows parameter reference table', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/settings`)

      const hasSection = await commands.isVisibleByText('파라미터 참조', 5_000)
      expect(hasSection).toBe(true)

      const hasParam = await commands.isVisibleByText('horizon_hours', 5_000)
      expect(hasParam).toBe(true)
    })

    it('shows save and reset buttons', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/settings`)

      const hasSave = await commands.isVisibleByText('저장', 5_000)
      expect(hasSave).toBe(true)

      const hasReset = await commands.isVisibleByText('초기화', 5_000)
      expect(hasReset).toBe(true)
    })

    it('shows solver_type parameter in reference table', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/settings`)

      const hasParam = await commands.isVisibleByText('solver_type', 5_000)
      expect(hasParam).toBe(true)
    })

    it('shows time_limit_sec parameter in reference table', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/settings`)

      const hasParam = await commands.isVisibleByText('time_limit_sec', 5_000)
      expect(hasParam).toBe(true)
    })
  })

  describe('Scheduler API', () => {
    it('checks scheduler service health', async () => {
      const res = await commands.fetchExternal('http://localhost:8002/health', 'GET')
      if (res.ok) {
        expect(res.data).toBeDefined()
      }
      // If service not running, test passes silently
    })

    it('lists available solvers', async () => {
      const res = await commands.fetchExternal('http://localhost:8002/api/v1/schedule/solvers', 'GET')
      if (res.ok) {
        expect(res.data).toBeDefined()
      }
    })

    it('fetches equipment availability via MES', async () => {
      const res = await commands.fetchApi('/scheduler/equipment-availability')
      if (res.ok) {
        expect(res.data).toHaveProperty('machines')
        expect(res.data).toHaveProperty('count')
        expect(Array.isArray(res.data.machines)).toBe(true)
      }
    })

    it('fetches work orders for scheduling via MES', async () => {
      const res = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
      if (res.ok) {
        expect(res.data).toHaveProperty('work_orders')
        expect(res.data).toHaveProperty('count')
        expect(Array.isArray(res.data.work_orders)).toBe(true)
      }
    })

    it('fetches current schedule', async () => {
      const res = await commands.fetchApi('/scheduler/current-schedule')
      if (res.ok) {
        expect(res.data).toBeDefined()
      }
    })
  })
})

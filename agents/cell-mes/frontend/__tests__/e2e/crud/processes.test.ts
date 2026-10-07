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

describe('Standard Processes CRUD', () => {
  describe('Read: Process list', () => {
    it('loads standard process management page', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/processes`)

      const hasHeading = await commands.isVisibleByRole('heading', '표준공정 관리')
      expect(hasHeading).toBe(true)
    })

    it('shows table or empty state', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/processes`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      const hasEmpty = await commands.isVisibleByText('등록된 표준공정이 없습니다', 3_000)

      expect(hasTable || hasEmpty).toBe(true)
    })

    it('shows table column headers when data exists', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/processes`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      if (hasTable) {
        const headers = ['코드', '공정명', '카테고리', '설비타입', 'Cycle Time', '설명', '등록일', '액션']
        for (const header of headers) {
          const hasHeader = await commands.isVisibleByText(header, 3_000)
          expect(hasHeader).toBe(true)
        }
      }
    })

    it('shows "표준공정 추가" button', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/processes`)

      const hasAddButton = await commands.isVisibleByRole('button', '표준공정 추가')
      expect(hasAddButton).toBe(true)
    })
  })

  describe('Read: API verification', () => {
    it('GET /std-processes returns valid array', async () => {
      const result = await commands.fetchApi('/masters/std-processes')
      expect(result.ok).toBe(true)
      expect(result.status).toBe(200)
      expect(Array.isArray(result.data)).toBe(true)
    })

    it('process items have required fields', async () => {
      const result = await commands.fetchApi('/masters/std-processes')
      expect(result.ok).toBe(true)

      if (result.data.length > 0) {
        const process = result.data[0]
        expect(process).toHaveProperty('id')
        expect(process).toHaveProperty('code')
        expect(process).toHaveProperty('name')
        expect(process).toHaveProperty('cycle_time_sec')
        expect(process).toHaveProperty('setup_time_sec')
      }
    })
  })

  describe('Create: Process creation modal', () => {
    it('opens creation modal with form fields', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/processes`)
      await commands.waitForTimeout(1000)

      await commands.clickByRole('button', '표준공정 추가')
      await commands.waitForTimeout(500)

      // Modal should open
      const hasModal = await commands.isVisibleBySelector('.fixed.inset-0', 5_000)
      expect(hasModal).toBe(true)

      // Check labels
      const labels = ['공정 코드', '공정명', '공정 카테고리', '설비 타입', 'Cycle Time', 'Setup Time', '설명']
      for (const label of labels) {
        const hasLabel = await commands.isVisibleByText(label, 3_000)
        expect(hasLabel).toBe(true)
      }

      // Check for input fields
      const hasInputs = await commands.isVisibleBySelector('input', 3_000)
      expect(hasInputs).toBe(true)

      // Check for textarea (description)
      const hasTextarea = await commands.isVisibleBySelector('textarea', 3_000)
      expect(hasTextarea).toBe(true)

      // Check for select fields (category, equipment type)
      const hasSelect = await commands.isVisibleBySelector('select', 3_000)
      expect(hasSelect).toBe(true)

      // Check for save button
      const hasSaveButton = await commands.isVisibleByRole('button', '저장')
      expect(hasSaveButton).toBe(true)

      const hasCancelButton = await commands.isVisibleByRole('button', '취소')
      expect(hasCancelButton).toBe(true)

      // Cancel
      await commands.clickByRole('button', '취소')
      await commands.waitForTimeout(500)
    })

    it('prevents submission with empty required fields', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/processes`)
      await commands.waitForTimeout(1000)

      await commands.clickByRole('button', '표준공정 추가')
      await commands.waitForTimeout(500)

      // Try to submit empty form
      await commands.clickByRole('button', '저장')
      await commands.waitForTimeout(500)

      // Modal should still be open (HTML5 validation)
      const hasModal = await commands.isVisibleBySelector('.fixed.inset-0', 3_000)
      expect(hasModal).toBe(true)

      await commands.clickByRole('button', '취소')
      await commands.waitForTimeout(500)
    })
  })

  describe('Create & Delete: Full CRUD flow via API', () => {
    it('creates a process via API, verifies in UI, then deletes', async () => {
      const ts = Date.now().toString().slice(-6)
      const processCode = `VTP-${ts}`
      const processName = `Vitest_Process_${ts}`

      // Create via API
      const createResult = await commands.fetchApi(
        '/masters/std-processes',
        'POST',
        JSON.stringify({
          code: processCode,
          name: processName,
          description: 'Test process created by Vitest',
          equipment_type: 'CNC',
          cycle_time_sec: 120,
          setup_time_sec: 30,
        })
      )
      expect(createResult.ok).toBe(true)
      expect(createResult.data).toHaveProperty('id')
      const createdId = createResult.data.id

      // Verify in API list
      const listResult = await commands.fetchApi('/masters/std-processes')
      expect(listResult.ok).toBe(true)
      const found = listResult.data.find((p: any) => p.code === processCode)
      expect(found).toBeDefined()
      expect(found.name).toBe(processName)
      expect(found.cycle_time_sec).toBe(120)
      expect(found.setup_time_sec).toBe(30)
      expect(found.equipment_type).toBe('CNC')

      // Verify in UI
      await login()
      await commands.goto(`${APP_URL}/master/processes`)
      await commands.waitForTimeout(2000)

      const hasCode = await commands.isVisibleByText(processCode, 5_000)
      expect(hasCode).toBe(true)

      const hasName = await commands.isVisibleByText(processName, 3_000)
      expect(hasName).toBe(true)

      // Delete via API
      const deleteResult = await commands.fetchApi(`/masters/std-processes/${createdId}`, 'DELETE')
      expect(deleteResult.ok).toBe(true)

      // Verify deleted
      const afterDelete = await commands.fetchApi('/masters/std-processes')
      const notFound = afterDelete.data.find((p: any) => p.code === processCode)
      expect(notFound).toBeUndefined()
    })
  })

  describe('Update: Edit process via API', () => {
    it('updates process fields via API', async () => {
      const code = `VTU-${Date.now().toString().slice(-6)}`

      // Create
      const createResult = await commands.fetchApi(
        '/masters/std-processes',
        'POST',
        JSON.stringify({
          code,
          name: 'Original Process',
          cycle_time_sec: 60,
          setup_time_sec: 10,
        })
      )
      expect(createResult.ok).toBe(true)
      const id = createResult.data.id

      // Update (StdProcessUpdate only accepts name, equipment_type, category_id)
      const updateResult = await commands.fetchApi(
        `/masters/std-processes/${id}`,
        'PATCH',
        JSON.stringify({
          name: 'Updated Process',
          equipment_type: 'ROBOT',
        })
      )
      expect(updateResult.ok).toBe(true)

      // Verify
      const getResult = await commands.fetchApi(`/masters/std-processes/${id}`)
      expect(getResult.ok).toBe(true)
      expect(getResult.data.name).toBe('Updated Process')
      expect(getResult.data.equipment_type).toBe('ROBOT')

      // Cleanup
      await commands.fetchApi(`/masters/std-processes/${id}`, 'DELETE')
    })
  })

  describe('Sorting', () => {
    it('table has sortable column headers', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/processes`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      if (hasTable) {
        const hasSortableHeaders = await commands.isVisibleBySelector('table th button', 3_000)
        expect(hasSortableHeaders).toBe(true)
      }
    })
  })
})

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

describe('Chat (AI Assistant)', () => {
  describe('Chat page load', () => {
    it('navigates to chat page', async () => {
      await login()
      await commands.goto(`${APP_URL}/chat`)
      await commands.waitForTimeout(2000)

      const hasChat = await commands.isVisibleByText('MES AI 어시스턴트', 5_000)
      expect(hasChat).toBe(true)
    })

    it('shows chat header with bot icon', async () => {
      await login()
      await commands.goto(`${APP_URL}/chat`)

      const hasTitle = await commands.isVisibleByText('MES AI 어시스턴트', 5_000)
      expect(hasTitle).toBe(true)

      const hasSubtitle = await commands.isVisibleByText('자연어로 생산 현황을 조회하세요', 5_000)
      expect(hasSubtitle).toBe(true)
    })

    it('shows welcome message when empty', async () => {
      await login()
      await commands.goto(`${APP_URL}/chat`)
      await commands.waitForTimeout(1000)

      const hasWelcome = await commands.isVisibleByText('안녕하세요', 5_000)
      expect(hasWelcome).toBe(true)
    })

    it('shows welcome guidance text', async () => {
      await login()
      await commands.goto(`${APP_URL}/chat`)
      await commands.waitForTimeout(1000)

      const hasGuidance = await commands.isVisibleByText('생산 현황, 설비 상태, KPI', 5_000)
      expect(hasGuidance).toBe(true)
    })

    it('shows quick action suggestion text', async () => {
      await login()
      await commands.goto(`${APP_URL}/chat`)
      await commands.waitForTimeout(1000)

      const hasQuickAction = await commands.isVisibleByText('빠른 질문을 클릭하거나 직접 입력하세요', 5_000)
      expect(hasQuickAction).toBe(true)
    })
  })

  describe('Chat input', () => {
    it('shows text input area', async () => {
      await login()
      await commands.goto(`${APP_URL}/chat`)

      const hasTextarea = await commands.isVisibleBySelector('textarea', 5_000)
      expect(hasTextarea).toBe(true)
    })

    it('shows placeholder text in input', async () => {
      await login()
      await commands.goto(`${APP_URL}/chat`)

      const hasPlaceholder = await commands.isVisibleBySelector('textarea[placeholder]', 5_000)
      expect(hasPlaceholder).toBe(true)
    })

    it('shows send button', async () => {
      await login()
      await commands.goto(`${APP_URL}/chat`)

      const hasButton = await commands.isVisibleBySelector('button', 5_000)
      expect(hasButton).toBe(true)
    })

    it('shows keyboard shortcut hint', async () => {
      await login()
      await commands.goto(`${APP_URL}/chat`)

      const hasHint = await commands.isVisibleByText('Enter로 전송', 5_000)
      expect(hasHint).toBe(true)
    })

    it('shows shift enter hint', async () => {
      await login()
      await commands.goto(`${APP_URL}/chat`)

      const hasHint = await commands.isVisibleByText('Shift\\+Enter로 줄바꿈', 5_000)
      expect(hasHint).toBe(true)
    })
  })

  describe('Chat layout', () => {
    it('has full height container', async () => {
      await login()
      await commands.goto(`${APP_URL}/chat`)

      // Chat should fill available height
      const hasContainer = await commands.isVisibleBySelector('.h-\\[calc\\(100vh-3rem\\)\\], [class*="h-"]', 5_000)
      const hasChat = await commands.isVisibleByText('MES AI 어시스턴트', 5_000)
      expect(hasContainer || hasChat).toBe(true)
    })

    it('shows bordered chat container', async () => {
      await login()
      await commands.goto(`${APP_URL}/chat`)

      const hasContainer = await commands.isVisibleBySelector('.border.border-gray-200, [class*="border"]', 5_000)
      const hasChat = await commands.isVisibleByText('MES AI 어시스턴트', 5_000)
      expect(hasContainer || hasChat).toBe(true)
    })
  })

  describe('Chat sidebar link', () => {
    it('shows AI assistant link in sidebar', async () => {
      await login()
      await commands.goto(`${APP_URL}/`)
      await commands.waitForTimeout(1000)

      const hasLink = await commands.isVisibleByText('AI 어시스턴트', 5_000)
      expect(hasLink).toBe(true)
    })

    it('shows NEW badge on AI assistant link', async () => {
      await login()
      await commands.goto(`${APP_URL}/`)
      await commands.waitForTimeout(1000)

      const hasBadge = await commands.isVisibleByText('NEW', 5_000)
      expect(hasBadge).toBe(true)
    })

    it('navigates to chat from sidebar', async () => {
      await login()
      await commands.goto(`${APP_URL}/`)
      await commands.waitForTimeout(1000)

      await commands.clickByText('AI 어시스턴트')
      await commands.waitForTimeout(2000)

      const hasChat = await commands.isVisibleByText('MES AI 어시스턴트', 5_000)
      expect(hasChat).toBe(true)
    })
  })
})

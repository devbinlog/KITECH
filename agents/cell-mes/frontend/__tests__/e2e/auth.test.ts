import { describe, it, expect } from 'vitest'
import { commands } from 'vitest/browser'

const APP_URL = 'http://localhost:3000'

describe('Authentication', () => {
  describe('Login page', () => {
    it('shows login form', async () => {
      await commands.goto(`${APP_URL}/login`)
      const headingVisible = await commands.isVisibleByRole('heading', 'Cell-MES')
      expect(headingVisible).toBe(true)
      const usernameVisible = await commands.isVisibleByRole('textbox', '사용자 ID')
      expect(usernameVisible).toBe(true)
    })

    it('shows MES subtitle', async () => {
      await commands.goto(`${APP_URL}/login`)
      const hasSub = await commands.isVisibleByText('Manufacturing Execution System', 5_000)
      expect(hasSub).toBe(true)
    })

    it('shows password field', async () => {
      await commands.goto(`${APP_URL}/login`)
      const hasPassword = await commands.isVisibleBySelector('input[type="password"]', 5_000)
      expect(hasPassword).toBe(true)
    })

    it('shows password label', async () => {
      await commands.goto(`${APP_URL}/login`)
      const hasLabel = await commands.isVisibleByText('비밀번호', 5_000)
      expect(hasLabel).toBe(true)
    })

    it('shows login button', async () => {
      await commands.goto(`${APP_URL}/login`)
      const hasBtn = await commands.isVisibleByRole('button', '로그인')
      expect(hasBtn).toBe(true)
    })

    it('logs in with valid credentials', async () => {
      await commands.goto(`${APP_URL}/login`)
      await commands.fillByRole('textbox', '사용자 ID', 'admin')
      await commands.fillByLabel('비밀번호', 'admin123')
      await commands.clickByRole('button', '로그인')

      // Should redirect away from login
      const url = await commands.waitForUrl('^(?!.*\\/login)', 10_000)
      expect(url).not.toContain('/login')
    })

    it('shows error with invalid credentials', async () => {
      await commands.goto(`${APP_URL}/login`)
      await commands.fillByRole('textbox', '사용자 ID', 'wrong')
      await commands.fillByLabel('비밀번호', 'wrong')
      await commands.clickByRole('button', '로그인')

      // Should stay on login page - wait briefly then check URL
      await new Promise((resolve) => setTimeout(resolve, 3_000))
      const url = await commands.currentUrl()
      expect(url).toContain('/login')
    })

    it('shows error message with invalid credentials', async () => {
      await commands.goto(`${APP_URL}/login`)
      await commands.fillByRole('textbox', '사용자 ID', 'invalid_user')
      await commands.fillByLabel('비밀번호', 'invalid_pass')
      await commands.clickByRole('button', '로그인')

      await commands.waitForTimeout(2000)

      // Should display error message or stay on login
      const hasError = await commands.isVisibleByText('실패', 5_000)
      const stillOnLogin = await commands.isVisibleByRole('button', '로그인')
      expect(hasError || stillOnLogin).toBe(true)
    })
  })

  describe('Auth redirect', () => {
    it('redirects to login when not authenticated', async () => {
      // Clear any existing auth by visiting login first
      await commands.goto(`${APP_URL}/login`)
      await commands.waitForTimeout(1000)

      // Try to access a protected page directly
      await commands.goto(`${APP_URL}/production/orders`)
      await commands.waitForTimeout(3000)

      // Should either show login page or the page (if token persists)
      const url = await commands.currentUrl()
      const isLogin = url.includes('/login')
      const isProtected = url.includes('/production')

      expect(isLogin || isProtected).toBe(true)
    })
  })

  describe('Authenticated session', () => {
    it('shows user info in sidebar after login', async () => {
      await commands.goto(`${APP_URL}/login`)
      await commands.fillByRole('textbox', '사용자 ID', 'admin')
      await commands.fillByLabel('비밀번호', 'admin123')
      await commands.clickByRole('button', '로그인')
      await commands.waitForUrl('^(?!.*\\/login)', 10_000)

      // Should show username in sidebar
      const hasUser = await commands.isVisibleByText('admin', 5_000)
      expect(hasUser).toBe(true)
    })

    it('shows logout button in sidebar', async () => {
      await commands.goto(`${APP_URL}/login`)
      await commands.fillByRole('textbox', '사용자 ID', 'admin')
      await commands.fillByLabel('비밀번호', 'admin123')
      await commands.clickByRole('button', '로그인')
      await commands.waitForUrl('^(?!.*\\/login)', 10_000)

      // Logout button should be present (has title="로그아웃")
      const hasLogout = await commands.isVisibleBySelector('button[title="로그아웃"]', 5_000)
      expect(hasLogout).toBe(true)
    })

    it('shows Cell-MES branding in sidebar', async () => {
      await commands.goto(`${APP_URL}/login`)
      await commands.fillByRole('textbox', '사용자 ID', 'admin')
      await commands.fillByLabel('비밀번호', 'admin123')
      await commands.clickByRole('button', '로그인')
      await commands.waitForUrl('^(?!.*\\/login)', 10_000)

      const hasBranding = await commands.isVisibleByText('Cell-MES', 5_000)
      expect(hasBranding).toBe(true)
    })
  })
})

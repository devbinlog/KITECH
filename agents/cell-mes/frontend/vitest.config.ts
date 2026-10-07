import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { playwright } from '@vitest/browser-playwright'
import path from 'path'
import {
  goto,
  currentUrl,
  fillByRole,
  fillByLabel,
  clickByRole,
  isVisibleByRole,
  waitForUrl,
  isVisibleByText,
  clickByText,
  waitForTimeout,
  isVisibleBySelector,
  closeAppPage,
  fetchApi,
  fetchExternal,
  acceptNextConfirm,
  selectOption,
  clickBySelector,
  fillBySelector,
  evaluateInPage,
} from './__tests__/e2e/commands/goto'

export default defineConfig({
  test: {
    projects: [
      {
        extends: true,
        plugins: [react()],
        test: {
          name: 'unit',
          environment: 'happy-dom',
          include: [
            '__tests__/unit/**/*.test.{ts,tsx}',
            '__tests__/components/**/*.test.{ts,tsx}',
          ],
          setupFiles: ['__tests__/setup.ts'],
          alias: {
            '@/generated': path.resolve(__dirname, './src/generated'),
            '@': path.resolve(__dirname, './'),
          },
        },
      },
      {
        test: {
          name: 'e2e',
          include: ['__tests__/e2e/**/*.test.ts'],
          browser: {
            enabled: true,
            provider: playwright(),
            instances: [{ browser: 'chromium' }],
            commands: {
              goto,
              currentUrl,
              fillByRole,
              fillByLabel,
              clickByRole,
              isVisibleByRole,
              waitForUrl,
              isVisibleByText,
              clickByText,
              waitForTimeout,
              isVisibleBySelector,
              closeAppPage,
              fetchApi,
              fetchExternal,
              acceptNextConfirm,
              selectOption,
              clickBySelector,
              fillBySelector,
              evaluateInPage,
            },
          },
          testTimeout: 60_000,
          hookTimeout: 30_000,
        },
      },
    ],
  },
})

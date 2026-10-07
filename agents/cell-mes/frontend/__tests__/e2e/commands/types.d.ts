/**
 * Type augmentation for custom browser commands.
 * This tells TypeScript about the custom commands registered in vitest.config.ts.
 */
declare module 'vitest/browser' {
  interface BrowserCommands {
    goto: (url: string) => Promise<void>
    currentUrl: () => Promise<string>
    fillByRole: (role: string, namePattern: string, value: string) => Promise<void>
    fillByLabel: (labelPattern: string, value: string) => Promise<void>
    clickByRole: (role: string, namePattern: string) => Promise<void>
    isVisibleByRole: (role: string, namePattern: string, timeout?: number) => Promise<boolean>
    waitForUrl: (urlPattern: string, timeout?: number) => Promise<string>
    isVisibleByText: (textPattern: string, timeout?: number) => Promise<boolean>
    clickByText: (textPattern: string) => Promise<void>
    waitForTimeout: (ms: number) => Promise<void>
    isVisibleBySelector: (selector: string, timeout?: number) => Promise<boolean>
    fetchApi: (path: string, method?: string, body?: string) => Promise<{ ok: boolean; status: number; data: any }>
    fetchExternal: (url: string, method?: string, body?: string) => Promise<{ ok: boolean; status: number; data: any }>
    acceptNextConfirm: () => Promise<void>
    selectOption: (selector: string, value: string) => Promise<void>
    clickBySelector: (selector: string) => Promise<void>
    fillBySelector: (selector: string, value: string) => Promise<void>
    evaluateInPage: (expression: string) => Promise<any>
    closeAppPage: () => Promise<void>
  }

  // Export commands object with the augmented BrowserCommands interface
  export const commands: BrowserCommands
}

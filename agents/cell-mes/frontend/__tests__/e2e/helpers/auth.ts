const API_BASE = 'http://localhost:8000/api/v1'
const APP_URL = 'http://localhost:3000'

export interface AuthToken {
  token: string
  user: { id: number; username: string; role: string }
}

export async function loginAsAdmin(): Promise<AuthToken> {
  const loginRes = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'username=admin&password=admin123',
  })
  if (!loginRes.ok) throw new Error(`Login failed: ${loginRes.status}`)
  const loginData = await loginRes.json()
  const token = loginData.access_token

  const meRes = await fetch(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!meRes.ok) throw new Error(`Get user failed: ${meRes.status}`)
  const user = await meRes.json()

  localStorage.setItem('token', token)
  localStorage.setItem('auth-storage', JSON.stringify({
    state: { user, isAuthenticated: true },
    version: 0,
  }))

  return { token, user }
}

export async function navigateAuthenticated(path: string = '/'): Promise<void> {
  const { commands } = await import('vitest/browser')
  await loginAsAdmin()
  await commands.goto(`${APP_URL}${path}`)
}

export function getApiHeaders(token: string): Record<string, string> {
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  }
}

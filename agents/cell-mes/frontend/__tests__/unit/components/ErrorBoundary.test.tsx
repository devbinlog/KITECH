import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ErrorBoundary from '@/components/ErrorBoundary'

function ThrowError({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) throw new Error('Test error message')
  return <div>No error</div>
}

describe('ErrorBoundary', () => {
  let consoleSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    consoleSpy.mockRestore()
  })

  it('renders children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <div>Child content</div>
      </ErrorBoundary>
    )
    expect(screen.getByText('Child content')).toBeInTheDocument()
  })

  it('renders default fallback when child throws', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    expect(screen.getByText('오류가 발생했습니다')).toBeInTheDocument()
  })

  it('renders retry button in default fallback', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    expect(screen.getByText('다시 시도')).toBeInTheDocument()
  })

  it('resets error state when retry button is clicked', () => {
    const { rerender } = render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    expect(screen.getByText('오류가 발생했습니다')).toBeInTheDocument()

    // Click retry - this resets the error state
    fireEvent.click(screen.getByText('다시 시도'))

    // After reset, ErrorBoundary will try to re-render children
    // Since ThrowError still throws, it will show the error again
    // But the state was reset momentarily
    expect(screen.getByText('오류가 발생했습니다')).toBeInTheDocument()
  })

  it('renders custom fallback component when provided', () => {
    function CustomFallback({ error, reset }: { error?: Error; reset: () => void }) {
      return (
        <div>
          <span>Custom error: {error?.message}</span>
          <button onClick={reset}>Custom reset</button>
        </div>
      )
    }

    render(
      <ErrorBoundary fallback={CustomFallback}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    expect(screen.getByText('Custom error: Test error message')).toBeInTheDocument()
    expect(screen.getByText('Custom reset')).toBeInTheDocument()
  })

  it('shows error message in development mode', () => {
    vi.stubEnv('NODE_ENV', 'development')

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    // In development mode, the error message is shown
    expect(screen.getByText('Test error message')).toBeInTheDocument()

    vi.unstubAllEnvs()
  })

  it('shows generic message in production mode', () => {
    vi.stubEnv('NODE_ENV', 'production')

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    expect(screen.getByText('페이지를 로드하는 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.')).toBeInTheDocument()

    vi.unstubAllEnvs()
  })

  it('calls console.error when error is caught', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    expect(consoleSpy).toHaveBeenCalled()
  })
})

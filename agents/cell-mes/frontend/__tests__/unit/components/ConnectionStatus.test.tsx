import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ConnectionBadge, {
  ServiceConnectionStatus,
  QualityConnectionCard,
} from '@/components/ConnectionStatus'

describe('ConnectionBadge (ConnectionStatus)', () => {
  it('renders title text', () => {
    render(<ConnectionBadge status="connected" title="서버 연결" />)
    expect(screen.getByText('서버 연결')).toBeInTheDocument()
  })

  it('renders with connected status styling', () => {
    const { container } = render(<ConnectionBadge status="connected" title="OK" />)
    expect(container.firstElementChild?.classList.toString()).toContain('bg-green-100')
  })

  it('renders with disconnected status styling', () => {
    const { container } = render(<ConnectionBadge status="disconnected" title="Fail" />)
    expect(container.firstElementChild?.classList.toString()).toContain('bg-red-100')
  })

  it('renders with warning status styling', () => {
    const { container } = render(<ConnectionBadge status="warning" title="Warn" />)
    expect(container.firstElementChild?.classList.toString()).toContain('bg-yellow-100')
  })

  it('renders with pending status styling', () => {
    const { container } = render(<ConnectionBadge status="pending" title="Wait" />)
    expect(container.firstElementChild?.classList.toString()).toContain('bg-blue-100')
  })

  it('renders count when provided', () => {
    render(<ConnectionBadge status="connected" title="Items" count={5} />)
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('does not render count when not provided', () => {
    const { container } = render(<ConnectionBadge status="connected" title="Items" />)
    const boldSpans = container.querySelectorAll('.font-bold')
    expect(boldSpans.length).toBe(0)
  })

  it('hides icon when showIcon is false', () => {
    const { container } = render(
      <ConnectionBadge status="connected" title="No Icon" showIcon={false} />
    )
    const svgs = container.querySelectorAll('svg')
    expect(svgs.length).toBe(0)
  })
})

describe('ServiceConnectionStatus', () => {
  it('renders service name', () => {
    render(<ServiceConnectionStatus serviceName="Cell-MES" isConnected={true} />)
    expect(screen.getByText('Cell-MES')).toBeInTheDocument()
  })

  it('renders connected badge when isConnected is true', () => {
    render(<ServiceConnectionStatus serviceName="MES" isConnected={true} />)
    expect(screen.getByText('연결됨')).toBeInTheDocument()
  })

  it('renders disconnected badge when isConnected is false', () => {
    render(<ServiceConnectionStatus serviceName="MES" isConnected={false} />)
    expect(screen.getByText('연결 안됨')).toBeInTheDocument()
  })

  it('shows url when provided', () => {
    render(
      <ServiceConnectionStatus
        serviceName="MES"
        isConnected={true}
        url="http://localhost:8000"
      />
    )
    expect(screen.getByText('http://localhost:8000')).toBeInTheDocument()
  })

  it('does not render url when not provided', () => {
    const { container } = render(
      <ServiceConnectionStatus serviceName="MES" isConnected={true} />
    )
    expect(container.querySelector('.text-xs.text-gray-500')).not.toBeInTheDocument()
  })
})

describe('QualityConnectionCard', () => {
  it('renders header title', () => {
    render(<QualityConnectionCard plansCount={10} resultsCount={8} connectedCount={7} />)
    expect(screen.getByText('검사계획 ↔ 측정결과 연결')).toBeInTheDocument()
  })

  it('renders plans count', () => {
    render(<QualityConnectionCard plansCount={10} resultsCount={8} connectedCount={7} />)
    expect(screen.getByText('10개')).toBeInTheDocument()
  })

  it('renders connected count', () => {
    render(<QualityConnectionCard plansCount={10} resultsCount={8} connectedCount={7} />)
    expect(screen.getByText('7개')).toBeInTheDocument()
  })

  it('renders unconnected count', () => {
    render(<QualityConnectionCard plansCount={10} resultsCount={8} connectedCount={7} />)
    expect(screen.getByText('3개')).toBeInTheDocument()
  })

  it('shows warning when connection rate is below 70%', () => {
    render(<QualityConnectionCard plansCount={10} resultsCount={3} connectedCount={3} />)
    expect(screen.getByText(/연결률이 낮습니다/)).toBeInTheDocument()
  })

  it('does not show warning when connection rate is above 70%', () => {
    render(<QualityConnectionCard plansCount={10} resultsCount={8} connectedCount={8} />)
    expect(screen.queryByText(/연결률이 낮습니다/)).not.toBeInTheDocument()
  })

  it('handles zero plans count without error', () => {
    render(<QualityConnectionCard plansCount={0} resultsCount={0} connectedCount={0} />)
    expect(screen.getByText('검사계획 ↔ 측정결과 연결')).toBeInTheDocument()
  })
})

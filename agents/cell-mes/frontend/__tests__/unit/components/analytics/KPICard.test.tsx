import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { KPICard } from '@/components/analytics/KPICard'
import { Activity, Package, AlertTriangle } from 'lucide-react'

describe('analytics/KPICard', () => {
  it('renders the title', () => {
    render(<KPICard title="OEE" value={85} icon={Activity} />)
    expect(screen.getByText('OEE')).toBeInTheDocument()
  })

  it('renders numeric value with locale formatting', () => {
    render(<KPICard title="생산량" value={12345} icon={Package} />)
    expect(screen.getByText('12,345')).toBeInTheDocument()
  })

  it('renders string value as-is', () => {
    render(<KPICard title="상태" value="Good" icon={Activity} />)
    expect(screen.getByText('Good')).toBeInTheDocument()
  })

  it('renders unit when provided', () => {
    render(<KPICard title="수율" value={95} unit="%" icon={Activity} />)
    expect(screen.getByText('%')).toBeInTheDocument()
  })

  it('does not render unit when not provided', () => {
    const { container } = render(<KPICard title="Count" value={10} icon={Activity} />)
    const unitElements = container.querySelectorAll('.text-sm.text-gray-500.font-medium')
    expect(unitElements.length).toBe(0)
  })

  it('renders description when provided', () => {
    render(
      <KPICard title="OEE" value={85} icon={Activity} description="Overall Equipment Effectiveness" />
    )
    expect(screen.getByText('Overall Equipment Effectiveness')).toBeInTheDocument()
  })

  it('renders target badge when target is provided', () => {
    render(<KPICard title="생산량" value={100} icon={Package} target={80} unit="개" />)
    expect(screen.getByText(/목표: 80/)).toBeInTheDocument()
  })

  it('shows green target badge when value meets target', () => {
    const { container } = render(
      <KPICard title="생산량" value={100} icon={Package} target={80} />
    )
    const targetBadge = container.querySelector('.bg-green-100')
    expect(targetBadge).toBeInTheDocument()
  })

  it('shows yellow target badge when value is below target', () => {
    const { container } = render(
      <KPICard title="생산량" value={50} icon={Package} target={80} />
    )
    const targetBadge = container.querySelector('.bg-yellow-100')
    expect(targetBadge).toBeInTheDocument()
  })

  it('renders trend indicator when trend and trendValue are provided', () => {
    render(
      <KPICard title="수율" value={95} icon={Activity} trend="up" trendValue="+5%" />
    )
    expect(screen.getByText('+5%')).toBeInTheDocument()
  })

  it('does not render trend section when trend is not provided', () => {
    const { container } = render(<KPICard title="수율" value={95} icon={Activity} />)
    const trendSection = container.querySelector('.mt-4.flex')
    expect(trendSection).not.toBeInTheDocument()
  })

  it('renders progress bar when target is provided with numeric value', () => {
    render(<KPICard title="생산량" value={60} icon={Package} target={100} />)
    expect(screen.getByText('진행률')).toBeInTheDocument()
    expect(screen.getByText('60%')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(
      <KPICard title="Test" value={1} icon={Activity} className="custom-kpi" />
    )
    expect(container.firstElementChild?.classList.toString()).toContain('custom-kpi')
  })

  it('defaults to blue color scheme', () => {
    const { container } = render(<KPICard title="Test" value={1} icon={Activity} />)
    expect(container.querySelector('.bg-blue-100')).toBeInTheDocument()
  })

  it('applies red color scheme', () => {
    const { container } = render(<KPICard title="Error" value={5} icon={AlertTriangle} color="red" />)
    expect(container.querySelector('.bg-red-100')).toBeInTheDocument()
  })
})

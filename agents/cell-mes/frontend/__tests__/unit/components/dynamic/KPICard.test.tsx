import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { KPICard } from '@/components/dynamic/KPICard'

describe('dynamic/KPICard', () => {
  it('renders title', () => {
    render(<KPICard title="생산량" value={100} />)
    expect(screen.getByText('생산량')).toBeInTheDocument()
  })

  it('renders numeric value with locale formatting', () => {
    render(<KPICard title="생산량" value={1234} />)
    expect(screen.getByText('1,234')).toBeInTheDocument()
  })

  it('renders string value as-is', () => {
    render(<KPICard title="상태" value="양호" />)
    expect(screen.getByText('양호')).toBeInTheDocument()
  })

  it('renders unit when provided', () => {
    render(<KPICard title="수율" value={95.5} unit="%" />)
    expect(screen.getByText('%')).toBeInTheDocument()
  })

  it('does not render unit when not provided', () => {
    const { container } = render(<KPICard title="개수" value={10} />)
    // Unit is rendered as a span sibling of the value inside .flex.items-baseline
    const baseline = container.querySelector('.flex.items-baseline')
    const spans = baseline?.querySelectorAll('span')
    // Only value span, no unit span
    expect(spans?.length).toBe(1)
  })

  it('renders trend indicator when trend is provided', () => {
    render(<KPICard title="OEE" value={85} trend="+5%" trendDirection="up" />)
    expect(screen.getByText('+5%')).toBeInTheDocument()
  })

  it('does not render trend indicator when trend is not provided', () => {
    const { container } = render(<KPICard title="OEE" value={85} />)
    // No trend text should appear
    expect(container.querySelector('.mt-2.text-sm')).not.toBeInTheDocument()
  })

  it('renders target with "달성" when value meets target', () => {
    render(<KPICard title="생산량" value={100} target={80} />)
    expect(screen.getByText('달성')).toBeInTheDocument()
  })

  it('renders target with "미달" when value is below target', () => {
    render(<KPICard title="생산량" value={50} target={80} />)
    expect(screen.getByText('미달')).toBeInTheDocument()
  })

  it('renders target value text', () => {
    render(<KPICard title="생산량" value={100} target={80} unit="개" />)
    expect(screen.getByText(/목표: 80/)).toBeInTheDocument()
  })

  it('applies color styling', () => {
    const { container } = render(<KPICard title="에러" value={5} color="red" />)
    expect(container.firstElementChild?.classList.toString()).toContain('bg-red-50')
  })

  it('defaults to blue color', () => {
    const { container } = render(<KPICard title="기본" value={10} />)
    expect(container.firstElementChild?.classList.toString()).toContain('bg-blue-50')
  })
})

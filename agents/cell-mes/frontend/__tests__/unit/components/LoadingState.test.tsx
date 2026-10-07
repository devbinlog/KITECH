import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import {
  LoadingSpinner,
  SkeletonCard,
  SkeletonChart,
  DashboardLoader,
  TableLoader,
  QualityDashboardLoader,
} from '@/components/LoadingState'

describe('LoadingSpinner', () => {
  it('renders default loading message', () => {
    render(<LoadingSpinner />)
    expect(screen.getByText('로딩 중...')).toBeInTheDocument()
  })

  it('renders custom message', () => {
    render(<LoadingSpinner message="데이터 불러오는 중..." />)
    expect(screen.getByText('데이터 불러오는 중...')).toBeInTheDocument()
  })

  it('applies small size class', () => {
    const { container } = render(<LoadingSpinner size="sm" />)
    const svg = container.querySelector('svg')
    expect(svg?.classList.toString()).toContain('h-4')
    expect(svg?.classList.toString()).toContain('w-4')
  })

  it('applies medium size class by default', () => {
    const { container } = render(<LoadingSpinner />)
    const svg = container.querySelector('svg')
    expect(svg?.classList.toString()).toContain('h-6')
    expect(svg?.classList.toString()).toContain('w-6')
  })

  it('applies large size class', () => {
    const { container } = render(<LoadingSpinner size="lg" />)
    const svg = container.querySelector('svg')
    expect(svg?.classList.toString()).toContain('h-8')
    expect(svg?.classList.toString()).toContain('w-8')
  })

  it('applies custom className', () => {
    const { container } = render(<LoadingSpinner className="my-custom-class" />)
    expect(container.firstElementChild?.classList.toString()).toContain('my-custom-class')
  })
})

describe('SkeletonCard', () => {
  it('renders with animate-pulse class', () => {
    const { container } = render(<SkeletonCard />)
    expect(container.firstElementChild?.classList.toString()).toContain('animate-pulse')
  })

  it('applies custom className', () => {
    const { container } = render(<SkeletonCard className="extra-class" />)
    expect(container.firstElementChild?.classList.toString()).toContain('extra-class')
  })
})

describe('SkeletonChart', () => {
  it('renders with default height', () => {
    const { container } = render(<SkeletonChart />)
    const inner = container.querySelector('.h-80')
    expect(inner).toBeInTheDocument()
  })

  it('renders with custom height', () => {
    const { container } = render(<SkeletonChart height="h-40" />)
    const inner = container.querySelector('.h-40')
    expect(inner).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(<SkeletonChart className="chart-skeleton" />)
    expect(container.firstElementChild?.classList.toString()).toContain('chart-skeleton')
  })
})

describe('DashboardLoader', () => {
  it('renders default dashboard message', () => {
    render(<DashboardLoader />)
    expect(screen.getByText('대시보드 로딩 중...')).toBeInTheDocument()
  })

  it('renders custom message', () => {
    render(<DashboardLoader message="커스텀 로딩..." />)
    expect(screen.getByText('커스텀 로딩...')).toBeInTheDocument()
  })

  it('renders 5 skeleton cards', () => {
    const { container } = render(<DashboardLoader />)
    const cards = container.querySelectorAll('.card.animate-pulse')
    expect(cards.length).toBeGreaterThanOrEqual(5)
  })
})

describe('TableLoader', () => {
  it('renders default 5 rows and 4 columns', () => {
    const { container } = render(<TableLoader />)
    // Header row + 5 data rows = 6 total grid containers
    const grids = container.querySelectorAll('[style*="grid-template-columns"]')
    // 1 header + 5 rows = 6
    expect(grids.length).toBe(6)
  })

  it('renders custom row and column counts', () => {
    const { container } = render(<TableLoader rows={3} columns={6} />)
    const grids = container.querySelectorAll('[style*="grid-template-columns"]')
    // 1 header + 3 rows = 4
    expect(grids.length).toBe(4)
  })

  it('applies custom className', () => {
    const { container } = render(<TableLoader className="table-loader" />)
    expect(container.firstElementChild?.classList.toString()).toContain('table-loader')
  })
})

describe('QualityDashboardLoader', () => {
  it('renders without crashing', () => {
    const { container } = render(<QualityDashboardLoader />)
    expect(container.firstElementChild).toBeInTheDocument()
  })

  it('renders skeleton cards for KPI section', () => {
    const { container } = render(<QualityDashboardLoader />)
    const cards = container.querySelectorAll('.card.animate-pulse')
    expect(cards.length).toBeGreaterThanOrEqual(5)
  })
})

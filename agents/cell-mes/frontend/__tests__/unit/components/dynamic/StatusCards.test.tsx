import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatusCards } from '@/components/dynamic/StatusCards'
import type { StatusCardItem } from '@/types/nlm'

const sampleItems: StatusCardItem[] = [
  { id: 'EQ-001', name: 'CNC Lathe 1', status: 'RUN', type: 'CNC' },
  { id: 'EQ-002', name: 'CNC Mill 2', status: 'IDLE', type: 'CNC' },
  { id: 'EQ-003', name: 'Robot Arm', status: 'ERROR', type: 'ROBOT' },
]

describe('StatusCards', () => {
  it('renders the title when provided', () => {
    render(<StatusCards title="설비 현황" items={sampleItems} />)
    expect(screen.getByText('설비 현황')).toBeInTheDocument()
  })

  it('renders all item names', () => {
    render(<StatusCards items={sampleItems} />)
    expect(screen.getByText('CNC Lathe 1')).toBeInTheDocument()
    expect(screen.getByText('CNC Mill 2')).toBeInTheDocument()
    expect(screen.getByText('Robot Arm')).toBeInTheDocument()
  })

  it('renders item IDs', () => {
    render(<StatusCards items={sampleItems} />)
    expect(screen.getByText('EQ-001')).toBeInTheDocument()
    expect(screen.getByText('EQ-002')).toBeInTheDocument()
    expect(screen.getByText('EQ-003')).toBeInTheDocument()
  })

  it('renders empty state when items is empty', () => {
    render(<StatusCards items={[]} />)
    expect(screen.getByText('설비 데이터가 없습니다')).toBeInTheDocument()
  })

  it('renders empty state when items is undefined', () => {
    render(<StatusCards items={undefined as any} />)
    expect(screen.getByText('설비 데이터가 없습니다')).toBeInTheDocument()
  })

  it('renders type badges for items with type', () => {
    render(<StatusCards items={sampleItems} />)
    const cncBadges = screen.getAllByText('CNC')
    expect(cncBadges.length).toBe(2)
    expect(screen.getByText('ROBOT')).toBeInTheDocument()
  })

  it('renders status labels', () => {
    render(<StatusCards items={sampleItems} />)
    const runLabels = screen.getAllByText('가동중')
    expect(runLabels.length).toBeGreaterThanOrEqual(1)
  })

  it('renders status summary in header when title is present', () => {
    render(<StatusCards title="Equipment" items={sampleItems} />)
    expect(screen.getByText(/가동중: 1/)).toBeInTheDocument()
    expect(screen.getByText(/대기: 1/)).toBeInTheDocument()
    expect(screen.getByText(/에러: 1/)).toBeInTheDocument()
  })

  it('renders metrics when provided', () => {
    const itemsWithMetrics: StatusCardItem[] = [
      {
        id: 'EQ-001',
        name: 'CNC 1',
        status: 'RUN',
        metrics: { spindle_rpm: 3000, load_percent: 75.3 },
      },
    ]
    render(<StatusCards items={itemsWithMetrics} />)
    expect(screen.getByText('RPM')).toBeInTheDocument()
    expect(screen.getByText('3,000')).toBeInTheDocument()
  })

  it('renders title in empty state when provided', () => {
    render(<StatusCards title="No Data Title" items={[]} />)
    expect(screen.getByText('No Data Title')).toBeInTheDocument()
  })
})

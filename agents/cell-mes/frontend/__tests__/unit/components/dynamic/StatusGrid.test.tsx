import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatusGrid } from '@/components/dynamic/StatusGrid'
import type { StatusItem } from '@/types/nlm'

const sampleItems: StatusItem[] = [
  { id: 'EQ-001', name: 'CNC Lathe 1', status: 'RUN', type: 'CNC' },
  { id: 'EQ-002', name: 'CNC Mill 2', status: 'IDLE', type: 'CNC' },
  { id: 'EQ-003', name: 'Robot Arm 1', status: 'ERROR', type: 'ROBOT' },
]

describe('StatusGrid', () => {
  it('renders the title when provided', () => {
    render(<StatusGrid title="설비 현황" items={sampleItems} />)
    expect(screen.getByText('설비 현황')).toBeInTheDocument()
  })

  it('renders all items', () => {
    render(<StatusGrid items={sampleItems} />)
    expect(screen.getByText('CNC Lathe 1')).toBeInTheDocument()
    expect(screen.getByText('CNC Mill 2')).toBeInTheDocument()
    expect(screen.getByText('Robot Arm 1')).toBeInTheDocument()
  })

  it('renders item IDs', () => {
    render(<StatusGrid items={sampleItems} />)
    expect(screen.getByText('EQ-001')).toBeInTheDocument()
    expect(screen.getByText('EQ-002')).toBeInTheDocument()
    expect(screen.getByText('EQ-003')).toBeInTheDocument()
  })

  it('renders empty state when items array is empty', () => {
    render(<StatusGrid items={[]} />)
    expect(screen.getByText('설비 데이터가 없습니다')).toBeInTheDocument()
  })

  it('renders empty state when items is undefined', () => {
    render(<StatusGrid items={undefined as any} />)
    expect(screen.getByText('설비 데이터가 없습니다')).toBeInTheDocument()
  })

  it('renders equipment type for items', () => {
    render(<StatusGrid items={sampleItems} />)
    const typeTexts = screen.getAllByText(/타입:/)
    expect(typeTexts.length).toBeGreaterThanOrEqual(1)
  })

  it('renders status labels', () => {
    render(<StatusGrid items={sampleItems} />)
    const runLabels = screen.getAllByText('가동중')
    expect(runLabels.length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('대기')).toBeInTheDocument()
    expect(screen.getByText('에러')).toBeInTheDocument()
  })

  it('renders status summary counts in header', () => {
    render(<StatusGrid title="설비" items={sampleItems} />)
    // Summary shows counts like "가동중: 1", "대기: 1", "에러: 1"
    expect(screen.getByText(/가동중: 1/)).toBeInTheDocument()
    expect(screen.getByText(/대기: 1/)).toBeInTheDocument()
    expect(screen.getByText(/에러: 1/)).toBeInTheDocument()
  })

  it('renders current job when provided', () => {
    const itemsWithJob: StatusItem[] = [
      { id: 'EQ-001', name: 'CNC 1', status: 'RUN', currentJob: 'WO-2024-001' },
    ]
    render(<StatusGrid items={itemsWithJob} />)
    expect(screen.getByText('WO-2024-001')).toBeInTheDocument()
  })

  it('renders metrics when provided', () => {
    const itemsWithMetrics: StatusItem[] = [
      {
        id: 'EQ-001',
        name: 'CNC 1',
        status: 'RUN',
        metrics: { spindle_rpm: 3000, load_percent: 75 },
      },
    ]
    render(<StatusGrid items={itemsWithMetrics} />)
    expect(screen.getByText('RPM:')).toBeInTheDocument()
  })
})

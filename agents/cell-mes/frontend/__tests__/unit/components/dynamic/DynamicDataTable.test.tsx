import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DynamicDataTable } from '@/components/dynamic/DynamicDataTable'

const sampleData = [
  { name: 'CNC-001', status: 'RUN', count: 150 },
  { name: 'CNC-002', status: 'IDLE', count: 80 },
  { name: 'CNC-003', status: 'ERROR', count: 0 },
]

const sampleColumns = ['name', 'status', 'count']

describe('DynamicDataTable', () => {
  it('renders the title when provided', () => {
    render(<DynamicDataTable columns={sampleColumns} data={sampleData} title="설비 목록" />)
    expect(screen.getByText('설비 목록')).toBeInTheDocument()
  })

  it('renders column headers from string array', () => {
    render(<DynamicDataTable columns={sampleColumns} data={sampleData} />)
    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Status')).toBeInTheDocument()
    expect(screen.getByText('Count')).toBeInTheDocument()
  })

  it('renders column headers from object array', () => {
    const columns = [
      { key: 'name', label: 'Equipment Name', sortable: true },
      { key: 'status', label: 'Current Status' },
    ]
    render(<DynamicDataTable columns={columns} data={sampleData} />)
    expect(screen.getByText('Equipment Name')).toBeInTheDocument()
    expect(screen.getByText('Current Status')).toBeInTheDocument()
  })

  it('renders data rows', () => {
    render(<DynamicDataTable columns={sampleColumns} data={sampleData} />)
    expect(screen.getByText('CNC-001')).toBeInTheDocument()
    expect(screen.getByText('CNC-002')).toBeInTheDocument()
    expect(screen.getByText('CNC-003')).toBeInTheDocument()
  })

  it('formats numeric values with locale', () => {
    render(<DynamicDataTable columns={sampleColumns} data={sampleData} />)
    expect(screen.getByText('150')).toBeInTheDocument()
  })

  it('shows empty state when data is empty', () => {
    render(<DynamicDataTable columns={sampleColumns} data={[]} />)
    expect(screen.getByText('데이터가 없습니다')).toBeInTheDocument()
  })

  it('renders search input when searchable is true', () => {
    render(<DynamicDataTable columns={sampleColumns} data={sampleData} searchable={true} />)
    expect(screen.getByPlaceholderText('검색...')).toBeInTheDocument()
  })

  it('does not render search input when searchable is false', () => {
    render(<DynamicDataTable columns={sampleColumns} data={sampleData} searchable={false} />)
    expect(screen.queryByPlaceholderText('검색...')).not.toBeInTheDocument()
  })

  it('filters data based on search input', () => {
    render(<DynamicDataTable columns={sampleColumns} data={sampleData} searchable={true} />)
    const input = screen.getByPlaceholderText('검색...')
    fireEvent.change(input, { target: { value: 'CNC-001' } })
    expect(screen.getByText('CNC-001')).toBeInTheDocument()
    expect(screen.queryByText('CNC-002')).not.toBeInTheDocument()
  })

  it('shows null/undefined as dash', () => {
    const dataWithNull = [{ name: 'Test', status: null, count: undefined }]
    render(
      <DynamicDataTable
        columns={sampleColumns}
        data={dataWithNull as any}
      />
    )
    const dashes = screen.getAllByText('-')
    expect(dashes.length).toBeGreaterThanOrEqual(2)
  })

  it('shows boolean values as Yes/No', () => {
    const dataWithBool = [{ name: 'Test', active: true, disabled: false }]
    render(
      <DynamicDataTable
        columns={['name', 'active', 'disabled']}
        data={dataWithBool as any}
      />
    )
    expect(screen.getByText('Yes')).toBeInTheDocument()
    expect(screen.getByText('No')).toBeInTheDocument()
  })

  it('does not render pagination when pagination is false', () => {
    render(
      <DynamicDataTable
        columns={sampleColumns}
        data={sampleData}
        pagination={false}
      />
    )
    expect(screen.queryByText(/개 중/)).not.toBeInTheDocument()
  })

  it('renders pagination when data exceeds page size', () => {
    const largeData = Array.from({ length: 15 }, (_, i) => ({
      name: `Item-${i}`,
      status: 'RUN',
      count: i,
    }))
    render(
      <DynamicDataTable
        columns={sampleColumns}
        data={largeData}
        pageSize={5}
      />
    )
    expect(screen.getByText('1 / 3')).toBeInTheDocument()
    expect(screen.getByText(/15개 중/)).toBeInTheDocument()
  })
})

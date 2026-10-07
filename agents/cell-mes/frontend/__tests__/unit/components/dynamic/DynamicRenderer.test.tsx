import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

// Mock the ComponentRegistry from the dynamic index
vi.mock('@/components/dynamic/index', () => ({
  ComponentRegistry: {
    KPICard: (props: any) => <div data-testid="kpi-card">{props.title}</div>,
    DataTable: (props: any) => <div data-testid="data-table">{props.title}</div>,
    StatusGrid: (props: any) => <div data-testid="status-grid">{props.title}</div>,
    StatusCards: (props: any) => <div data-testid="status-cards">{props.title}</div>,
  },
}))

import { DynamicRenderer } from '@/components/dynamic/DynamicRenderer'
import type { UISchema } from '@/types/nlm'

describe('DynamicRenderer', () => {
  it('renders nothing when schema is null', () => {
    const { container } = render(<DynamicRenderer schema={null as any} />)
    expect(container.innerHTML).toBe('')
  })

  it('renders nothing when schema has no components', () => {
    const schema: UISchema = { layout: 'single', components: [] }
    const { container } = render(<DynamicRenderer schema={schema} />)
    expect(container.innerHTML).toBe('')
  })

  it('renders schema title when provided', () => {
    const schema: UISchema = {
      layout: 'single',
      title: 'Dashboard Title',
      components: [
        { type: 'KPICard', props: { title: 'Test KPI', value: 100 } },
      ],
    }
    render(<DynamicRenderer schema={schema} />)
    expect(screen.getByText('Dashboard Title')).toBeInTheDocument()
  })

  it('renders KPICard component from registry', () => {
    const schema: UISchema = {
      layout: 'dashboard',
      components: [
        { type: 'KPICard', props: { title: 'Production Count', value: 500 } },
      ],
    }
    render(<DynamicRenderer schema={schema} />)
    expect(screen.getByTestId('kpi-card')).toBeInTheDocument()
    expect(screen.getByText('Production Count')).toBeInTheDocument()
  })

  it('renders DataTable component from registry', () => {
    const schema: UISchema = {
      layout: 'single',
      components: [
        {
          type: 'DataTable',
          props: { title: 'Work Orders', columns: ['id'], data: [] },
        },
      ],
    }
    render(<DynamicRenderer schema={schema} />)
    expect(screen.getByTestId('data-table')).toBeInTheDocument()
    expect(screen.getByText('Work Orders')).toBeInTheDocument()
  })

  it('renders multiple components', () => {
    const schema: UISchema = {
      layout: 'dashboard',
      components: [
        { type: 'KPICard', props: { title: 'KPI 1', value: 10 } },
        { type: 'KPICard', props: { title: 'KPI 2', value: 20 } },
        { type: 'StatusGrid', props: { title: 'Grid', items: [] } },
      ],
    }
    render(<DynamicRenderer schema={schema} />)
    expect(screen.getByText('KPI 1')).toBeInTheDocument()
    expect(screen.getByText('KPI 2')).toBeInTheDocument()
    expect(screen.getByText('Grid')).toBeInTheDocument()
  })

  it('renders error for unknown component type', () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const schema: UISchema = {
      layout: 'single',
      components: [
        { type: 'UnknownWidget', props: {} },
      ],
    }
    render(<DynamicRenderer schema={schema} />)
    expect(screen.getByText(/Unknown component: UnknownWidget/)).toBeInTheDocument()
    consoleSpy.mockRestore()
  })

  it('applies dashboard layout class', () => {
    const schema: UISchema = {
      layout: 'dashboard',
      components: [
        { type: 'KPICard', props: { title: 'Test', value: 1 } },
      ],
    }
    const { container } = render(<DynamicRenderer schema={schema} />)
    const layoutDiv = container.querySelector('.grid.grid-cols-1')
    expect(layoutDiv).toBeInTheDocument()
  })

  it('does not render title when not provided in schema', () => {
    const schema: UISchema = {
      layout: 'single',
      components: [
        { type: 'KPICard', props: { title: 'Test', value: 1 } },
      ],
    }
    const { container } = render(<DynamicRenderer schema={schema} />)
    const h3 = container.querySelector('h3')
    expect(h3).not.toBeInTheDocument()
  })
})

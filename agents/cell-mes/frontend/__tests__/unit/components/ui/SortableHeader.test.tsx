import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SortableHeader } from '@/components/ui/SortableHeader'

describe('SortableHeader', () => {
  const defaultProps = {
    label: 'Name',
    field: 'name',
    currentSort: '',
    currentOrder: 'asc' as const,
    onSort: vi.fn(),
  }

  it('renders the label text', () => {
    render(<SortableHeader {...defaultProps} />)
    expect(screen.getByText('Name')).toBeInTheDocument()
  })

  it('renders as a button element', () => {
    render(<SortableHeader {...defaultProps} />)
    expect(screen.getByRole('button', { name: /Name/ })).toBeInTheDocument()
  })

  it('calls onSort with the field when clicked', () => {
    const onSort = vi.fn()
    render(<SortableHeader {...defaultProps} onSort={onSort} />)
    fireEvent.click(screen.getByRole('button'))
    expect(onSort).toHaveBeenCalledWith('name')
  })

  it('shows neutral icon when field is not active sort', () => {
    const { container } = render(
      <SortableHeader {...defaultProps} currentSort="other_field" />
    )
    // ArrowUpDown icon should be rendered (neutral state) with text-gray-400
    const svgs = container.querySelectorAll('svg')
    expect(svgs.length).toBe(1)
    expect(svgs[0].classList.toString()).toContain('text-gray-400')
  })

  it('shows ascending icon when field is active and order is asc', () => {
    const { container } = render(
      <SortableHeader {...defaultProps} currentSort="name" currentOrder="asc" />
    )
    // ArrowUp icon rendered - no text-gray-400 class
    const svgs = container.querySelectorAll('svg')
    expect(svgs.length).toBe(1)
    expect(svgs[0].classList.toString()).not.toContain('text-gray-400')
  })

  it('shows descending icon when field is active and order is desc', () => {
    const { container } = render(
      <SortableHeader {...defaultProps} currentSort="name" currentOrder="desc" />
    )
    const svgs = container.querySelectorAll('svg')
    expect(svgs.length).toBe(1)
    expect(svgs[0].classList.toString()).not.toContain('text-gray-400')
  })

  it('applies custom className', () => {
    render(<SortableHeader {...defaultProps} className="custom-header" />)
    const button = screen.getByRole('button')
    expect(button.classList.toString()).toContain('custom-header')
  })
})

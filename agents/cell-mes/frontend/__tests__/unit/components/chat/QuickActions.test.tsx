import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QuickActions } from '@/components/chat/QuickActions'

describe('QuickActions', () => {
  it('renders the section title', () => {
    render(<QuickActions onSelect={vi.fn()} />)
    expect(screen.getByText('자주 묻는 질문')).toBeInTheDocument()
  })

  it('renders all 6 quick action buttons', () => {
    render(<QuickActions onSelect={vi.fn()} />)
    expect(screen.getByText('오늘 생산 현황')).toBeInTheDocument()
    expect(screen.getByText('설비 상태')).toBeInTheDocument()
    expect(screen.getByText('가동률')).toBeInTheDocument()
    expect(screen.getByText('이번 주 수율')).toBeInTheDocument()
    expect(screen.getByText('작업지시 목록')).toBeInTheDocument()
    expect(screen.getByText('오늘 스케줄')).toBeInTheDocument()
  })

  it('calls onSelect with the correct query when a button is clicked', () => {
    const onSelect = vi.fn()
    render(<QuickActions onSelect={onSelect} />)
    fireEvent.click(screen.getByText('설비 상태'))
    expect(onSelect).toHaveBeenCalledWith('설비 상태 조회')
  })

  it('calls onSelect with production query when first button is clicked', () => {
    const onSelect = vi.fn()
    render(<QuickActions onSelect={onSelect} />)
    fireEvent.click(screen.getByText('오늘 생산 현황'))
    expect(onSelect).toHaveBeenCalledWith('오늘 생산 현황 보여줘')
  })

  it('disables all buttons when disabled prop is true', () => {
    render(<QuickActions onSelect={vi.fn()} disabled={true} />)
    const buttons = screen.getAllByRole('button')
    buttons.forEach((button) => {
      expect(button).toBeDisabled()
    })
  })

  it('does not call onSelect when disabled button is clicked', () => {
    const onSelect = vi.fn()
    render(<QuickActions onSelect={onSelect} disabled={true} />)
    fireEvent.click(screen.getByText('설비 상태'))
    expect(onSelect).not.toHaveBeenCalled()
  })

  it('enables all buttons by default', () => {
    render(<QuickActions onSelect={vi.fn()} />)
    const buttons = screen.getAllByRole('button')
    buttons.forEach((button) => {
      expect(button).not.toBeDisabled()
    })
  })
})

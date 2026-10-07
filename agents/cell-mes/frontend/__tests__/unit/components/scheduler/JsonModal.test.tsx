import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { JsonModal } from '@/components/scheduler/JsonModal'

describe('JsonModal', () => {
  const defaultProps = {
    isOpen: true,
    title: 'Test Data',
    data: { key: 'value', count: 42 },
    onClose: vi.fn(),
  }

  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders nothing when isOpen is false', () => {
    const { container } = render(<JsonModal {...defaultProps} isOpen={false} />)
    expect(container.innerHTML).toBe('')
  })

  it('renders nothing when data is null', () => {
    const { container } = render(<JsonModal {...defaultProps} data={null} />)
    expect(container.innerHTML).toBe('')
  })

  it('renders the title', () => {
    render(<JsonModal {...defaultProps} />)
    expect(screen.getByText('Test Data')).toBeInTheDocument()
  })

  it('renders JSON data in a pre element', () => {
    const { container } = render(<JsonModal {...defaultProps} />)
    const pre = container.querySelector('pre')
    expect(pre).toBeInTheDocument()
    expect(pre?.textContent).toContain('"key": "value"')
    expect(pre?.textContent).toContain('"count": 42')
  })

  it('renders download button', () => {
    render(<JsonModal {...defaultProps} />)
    expect(screen.getByText('다운로드')).toBeInTheDocument()
  })

  it('renders close button', () => {
    render(<JsonModal {...defaultProps} />)
    const closeButton = screen.getByText('\u2715')
    expect(closeButton).toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', () => {
    const onClose = vi.fn()
    render(<JsonModal {...defaultProps} onClose={onClose} />)
    fireEvent.click(screen.getByText('\u2715'))
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('triggers download when download button is clicked', () => {
    const createObjectURL = vi.fn(() => 'blob:test')
    const revokeObjectURL = vi.fn()
    global.URL.createObjectURL = createObjectURL
    global.URL.revokeObjectURL = revokeObjectURL

    const clickMock = vi.fn()

    // Render first, then spy on createElement so the mock isn't consumed by render()
    render(<JsonModal {...defaultProps} />)

    vi.spyOn(document, 'createElement').mockReturnValueOnce({
      href: '',
      download: '',
      click: clickMock,
      set setAttribute(_: string) {},
    } as unknown as HTMLAnchorElement)

    fireEvent.click(screen.getByText('다운로드'))

    expect(createObjectURL).toHaveBeenCalled()
    expect(clickMock).toHaveBeenCalled()
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:test')
  })

  it('displays nested JSON data correctly', () => {
    const nestedData = {
      schedule: [
        { id: 1, name: 'Task 1' },
        { id: 2, name: 'Task 2' },
      ],
    }
    const { container } = render(<JsonModal {...defaultProps} data={nestedData} />)
    const pre = container.querySelector('pre')
    expect(pre).toBeInTheDocument()
    expect(pre?.textContent).toContain('"name": "Task 1"')
    expect(pre?.textContent).toContain('"name": "Task 2"')
  })
})

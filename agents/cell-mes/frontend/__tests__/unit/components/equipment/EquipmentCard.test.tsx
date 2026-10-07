import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { EquipmentCard } from '@/components/equipment/EquipmentCard'
import type { Equipment } from '@/types'

function makeEquipment(overrides: Partial<Equipment> = {}): Equipment {
  return {
    id: 1,
    eq_code: 'EQ-001',
    aas_id: null,
    eq_name: 'CNC Lathe 1',
    model_name: 'Model X',
    equipment_type: 'CNC',
    location: 'Cell A',
    cell_id: 1,
    connection_config: {},
    spec_data: {},
    last_data: {},
    current_status: 'RUN',
    updated_at: '2026-01-01T00:00:00Z',
    last_connected_at: null,
    is_deleted: false,
    ...overrides,
  }
}

describe('EquipmentCard', () => {
  it('renders equipment name', () => {
    render(<EquipmentCard equipment={makeEquipment()} />)
    expect(screen.getByText('CNC Lathe 1')).toBeInTheDocument()
  })

  it('renders equipment type', () => {
    render(<EquipmentCard equipment={makeEquipment()} />)
    expect(screen.getByText('CNC')).toBeInTheDocument()
  })

  it('renders RUN status label', () => {
    render(<EquipmentCard equipment={makeEquipment({ current_status: 'RUN' })} />)
    expect(screen.getByText('가동중')).toBeInTheDocument()
  })

  it('renders STOP status label', () => {
    render(<EquipmentCard equipment={makeEquipment({ current_status: 'STOP' })} />)
    expect(screen.getByText('정지')).toBeInTheDocument()
  })

  it('renders ERROR status label', () => {
    render(<EquipmentCard equipment={makeEquipment({ current_status: 'ERROR' })} />)
    expect(screen.getByText('에러')).toBeInTheDocument()
  })

  it('calls onClick when card is clicked', () => {
    const onClick = vi.fn()
    render(<EquipmentCard equipment={makeEquipment()} onClick={onClick} />)
    fireEvent.click(screen.getByText('CNC Lathe 1').closest('.card')!)
    expect(onClick).toHaveBeenCalledOnce()
  })

  it('renders middleware CNC status data when available', () => {
    const equipment = makeEquipment({
      equipment_type: 'CNC',
      last_data: {
        cncGateway: { status: { machinePositionX: 12.3, doorState: 'closed' } },
        modbusGateway: { status: { viseState: 'clamp' } },
      },
    })
    render(<EquipmentCard equipment={equipment} />)
    expect(screen.getByText('도어 상태')).toBeInTheDocument()
    expect(screen.getByText('닫힘')).toBeInTheDocument()
    expect(screen.getByText('바이스 상태')).toBeInTheDocument()
    expect(screen.getByText('클램프')).toBeInTheDocument()
    expect(screen.getByText('12.3 mm')).toBeInTheDocument()
  })

  it('does not render middleware detail rows when values are missing', () => {
    const equipment = makeEquipment({
      equipment_type: 'CNC',
      last_data: {},
    })
    render(<EquipmentCard equipment={equipment} />)
    expect(screen.queryByText('도어 상태')).not.toBeInTheDocument()
    expect(screen.queryByText('바이스 상태')).not.toBeInTheDocument()
  })

  it('renders middleware ROBOT status data when available', () => {
    const equipment = makeEquipment({
      equipment_type: 'ROBOT',
      last_data: {
        robotGateway: { status: { status: 'BUSY', agvPositionX: 1.2, agvPositionY: 3.4 } },
      },
    })
    render(<EquipmentCard equipment={equipment} />)
    expect(screen.getByText('동작 상태')).toBeInTheDocument()
    expect(screen.getByText('작업중')).toBeInTheDocument()
    expect(screen.getByText('AGV 위치')).toBeInTheDocument()
    expect(screen.getByText('X:1.2 Y:3.4')).toBeInTheDocument()
  })

  it('renders ROBOT idle state from middleware status', () => {
    const equipment = makeEquipment({
      equipment_type: 'ROBOT',
      last_data: {
        robotGateway: { status: { status: 'IDLE' } },
      },
    })
    render(<EquipmentCard equipment={equipment} />)
    expect(screen.getByText('대기')).toBeInTheDocument()
  })

  it('renders virtual equipment badge and scheduler machine type', () => {
    const equipment = makeEquipment({
      eq_name: 'NX5500_VIRTUAL_01',
      equipment_type: 'CNC',
      spec_data: {
        isVirtual: true,
        equipmentSource: 'VIRTUAL',
        machineType: 'VMC_3AXIS_MASS',
      },
    })
    render(<EquipmentCard equipment={equipment} />)
    expect(screen.getByText('가상장비')).toBeInTheDocument()
    expect(screen.getByText(/VMC_3AXIS_MASS/)).toBeInTheDocument()
  })

  it('renders AAS ID when provided', () => {
    const equipment = makeEquipment({ aas_id: 'urn:aas:example:001' })
    render(<EquipmentCard equipment={equipment} />)
    expect(screen.getByText('AAS: urn:aas:example:001')).toBeInTheDocument()
  })

  it('does not render AAS ID when not provided', () => {
    const equipment = makeEquipment({ aas_id: null })
    render(<EquipmentCard equipment={equipment} />)
    expect(screen.queryByText(/AAS:/)).not.toBeInTheDocument()
  })
})

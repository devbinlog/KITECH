import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import {
  ConnectionBadge,
  ServiceBadge,
  RoutingStatus,
  ProductStatusBadge,
} from '@/components/ui/ConnectionBadge'

describe('ConnectionBadge', () => {
  it('renders routing count when hasRouting is true', () => {
    render(<ConnectionBadge hasRouting={true} routingCount={3} />)
    expect(screen.getByText('3개 공정')).toBeInTheDocument()
  })

  it('renders green background when hasRouting is true', () => {
    const { container } = render(<ConnectionBadge hasRouting={true} routingCount={3} />)
    expect(container.firstElementChild?.classList.toString()).toContain('bg-green-100')
  })

  it('renders "라우팅 없음" when hasRouting is false', () => {
    render(<ConnectionBadge hasRouting={false} routingCount={0} />)
    expect(screen.getByText('라우팅 없음')).toBeInTheDocument()
  })

  it('renders yellow background when hasRouting is false', () => {
    const { container } = render(<ConnectionBadge hasRouting={false} routingCount={0} />)
    expect(container.firstElementChild?.classList.toString()).toContain('bg-yellow-100')
  })

  it('applies custom className', () => {
    const { container } = render(
      <ConnectionBadge hasRouting={true} routingCount={1} className="custom-class" />
    )
    expect(container.firstElementChild?.classList.toString()).toContain('custom-class')
  })
})

describe('ServiceBadge', () => {
  it('renders connected status text', () => {
    render(<ServiceBadge status="connected" serviceName="Cell-MES" />)
    expect(screen.getByText('연결됨')).toBeInTheDocument()
  })

  it('renders disconnected status text', () => {
    render(<ServiceBadge status="disconnected" serviceName="Cell-MES" />)
    expect(screen.getByText('연결 안됨')).toBeInTheDocument()
  })

  it('renders checking status text', () => {
    render(<ServiceBadge status="checking" serviceName="Cell-MES" />)
    expect(screen.getByText('확인 중')).toBeInTheDocument()
  })

  it('shows service name when url is provided', () => {
    render(<ServiceBadge status="connected" serviceName="Cell-MES" url="http://localhost:8000" />)
    expect(screen.getByText('Cell-MES')).toBeInTheDocument()
  })

  it('does not show service name when url is not provided', () => {
    render(<ServiceBadge status="connected" serviceName="Cell-MES" />)
    expect(screen.queryByText('Cell-MES')).not.toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(
      <ServiceBadge status="connected" serviceName="MES" className="my-badge" />
    )
    expect(container.firstElementChild?.classList.toString()).toContain('my-badge')
  })
})

describe('RoutingStatus', () => {
  it('renders ConnectionBadge with routing', () => {
    render(<RoutingStatus routingCount={2} />)
    expect(screen.getByText('2개 공정')).toBeInTheDocument()
  })

  it('shows detail text when showDetails is true and has routing', () => {
    render(<RoutingStatus routingCount={2} showDetails={true} />)
    expect(screen.getByText('작업지시 생성 가능')).toBeInTheDocument()
  })

  it('shows warning detail when showDetails is true and no routing', () => {
    render(<RoutingStatus routingCount={0} showDetails={true} />)
    expect(screen.getByText('작업지시 생성 불가')).toBeInTheDocument()
  })

  it('does not show detail text when showDetails is false', () => {
    render(<RoutingStatus routingCount={2} showDetails={false} />)
    expect(screen.queryByText('작업지시 생성 가능')).not.toBeInTheDocument()
  })
})

describe('ProductStatusBadge', () => {
  it('renders routing status with details', () => {
    render(<ProductStatusBadge productCode="P001" routingCount={3} />)
    expect(screen.getByText('3개 공정')).toBeInTheDocument()
    expect(screen.getByText('작업지시 생성 가능')).toBeInTheDocument()
  })

  it('shows active order badge when hasActiveOrders is true', () => {
    render(<ProductStatusBadge productCode="P001" routingCount={1} hasActiveOrders={true} />)
    expect(screen.getByText('생산 중')).toBeInTheDocument()
  })

  it('does not show active order badge when hasActiveOrders is false', () => {
    render(<ProductStatusBadge productCode="P001" routingCount={1} hasActiveOrders={false} />)
    expect(screen.queryByText('생산 중')).not.toBeInTheDocument()
  })
})

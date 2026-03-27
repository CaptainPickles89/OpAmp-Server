import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { HealthBadge } from '../HealthBadge'

describe('HealthBadge', () => {
  it('renders "Healthy" text for status=healthy', () => {
    render(<HealthBadge status="healthy" />)
    expect(screen.getByText('Healthy')).toBeTruthy()
  })

  it('renders "Degraded" text for status=degraded', () => {
    render(<HealthBadge status="degraded" />)
    expect(screen.getByText('Degraded')).toBeTruthy()
  })

  it('renders "Unhealthy" text for status=unhealthy', () => {
    render(<HealthBadge status="unhealthy" />)
    expect(screen.getByText('Unhealthy')).toBeTruthy()
  })

  it('renders "Unknown" text for status=unknown', () => {
    render(<HealthBadge status="unknown" />)
    expect(screen.getByText('Unknown')).toBeTruthy()
  })

  it('does not rely on color alone (text is always present)', () => {
    render(<HealthBadge status="healthy" />)
    const wrapper = screen.getByText('Healthy').closest('span')
    expect(wrapper).toBeTruthy()
    expect(wrapper?.textContent).toContain('Healthy')
  })

  it('sets aria-label to the status value', () => {
    const { container } = render(<HealthBadge status="degraded" />)
    const badge = container.querySelector('[aria-label="degraded"]')
    expect(badge).toBeTruthy()
  })
})

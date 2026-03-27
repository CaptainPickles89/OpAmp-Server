import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { PushStatusBadge } from '../PushStatusBadge'

describe('PushStatusBadge', () => {
  it('renders nothing for IDLE state', () => {
    const { container } = render(<PushStatusBadge pushState="IDLE" />)
    expect(container.firstChild).toBeNull()
  })

  it('renders amber "Push Pending" for PUSH_PENDING', () => {
    render(<PushStatusBadge pushState="PUSH_PENDING" />)
    expect(screen.getByText('Push Pending')).toBeTruthy()
  })

  it('renders blue pulsing "Applying..." for APPLYING', () => {
    render(<PushStatusBadge pushState="APPLYING" />)
    expect(screen.getByText('Applying...')).toBeTruthy()
  })

  it('renders green "Applied" for APPLIED', () => {
    render(<PushStatusBadge pushState="APPLIED" />)
    expect(screen.getByText('Applied')).toBeTruthy()
  })

  it('renders red "Failed" for FAILED', () => {
    render(<PushStatusBadge pushState="FAILED" />)
    expect(screen.getByText('Failed')).toBeTruthy()
  })

  it('APPLYING badge has aria-live="polite" for screen reader updates', () => {
    const { container } = render(<PushStatusBadge pushState="APPLYING" />)
    const badge = container.querySelector('[aria-live="polite"]')
    expect(badge).toBeTruthy()
  })
})

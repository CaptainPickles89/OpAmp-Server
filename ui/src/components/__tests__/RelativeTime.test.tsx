import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { RelativeTime } from '../RelativeTime'

describe('RelativeTime', () => {
  it('displays "just now" for timestamps within 10 seconds', () => {
    const ns = (Date.now() - 3000) * 1_000_000
    render(<RelativeTime nanoseconds={ns} />)
    expect(screen.getByText('just now')).toBeTruthy()
  })

  it('displays "X minutes ago" for timestamps 1-59 minutes old', () => {
    const ns = (Date.now() - 5 * 60 * 1000) * 1_000_000
    render(<RelativeTime nanoseconds={ns} />)
    const el = screen.getByText(/minute/)
    expect(el).toBeTruthy()
  })

  it('displays full ISO timestamp in title attribute', () => {
    const ms = Date.now() - 60000
    const ns = ms * 1_000_000
    const { container } = render(<RelativeTime nanoseconds={ns} />)
    // Check that a time element exists with a title attribute containing the ISO date
    const timeEl = container.querySelector('time[title]')
    expect(timeEl).toBeTruthy()
    const title = timeEl?.getAttribute('title') ?? ''
    expect(title).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/)
  })
})

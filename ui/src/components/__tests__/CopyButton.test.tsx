import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { CopyButton } from '../CopyButton'

describe('CopyButton', () => {
  beforeEach(() => {
    // Mock clipboard API
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: vi.fn().mockResolvedValue(undefined) },
      writable: true,
      configurable: true,
    })
  })

  it('renders "Copy" initially', () => {
    render(<CopyButton text="hello" />)
    expect(screen.getByText('Copy')).toBeTruthy()
  })

  it('changes to "Copied!" after click', async () => {
    render(<CopyButton text="hello" />)
    fireEvent.click(screen.getByRole('button'))
    await waitFor(() => {
      expect(screen.getByText('Copied!')).toBeTruthy()
    })
  })

  it('resets to "Copy" after 2 seconds', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    render(<CopyButton text="hello" />)
    fireEvent.click(screen.getByRole('button'))
    // Wait for 'Copied!' to appear (clipboard promise resolves)
    await waitFor(() => expect(screen.queryByText('Copied!')).not.toBeNull(), { timeout: 1000 })
    // Fast-forward 2.1 seconds
    vi.advanceTimersByTime(2100)
    await waitFor(() => expect(screen.queryByText('Copy')).not.toBeNull(), { timeout: 1000 })
    vi.useRealTimers()
  })

  it('calls navigator.clipboard.writeText with correct text', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      writable: true,
      configurable: true,
    })
    render(<CopyButton text="copy me" />)
    fireEvent.click(screen.getByRole('button'))
    expect(writeText).toHaveBeenCalledWith('copy me')
  })
})

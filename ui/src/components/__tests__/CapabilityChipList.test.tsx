import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { CapabilityChipList, decodeCapabilities } from '../CapabilityChipList'

describe('decodeCapabilities', () => {
  it('returns [{label: "None", variant: "hex"}] for 0', () => {
    const result = decodeCapabilities(0)
    expect(result).toEqual([{ label: 'None', variant: 'hex' }])
  })

  it('returns Remote Config and Health for capabilities=6 (0x0002 | 0x0004)', () => {
    const result = decodeCapabilities(6)
    expect(result).toHaveLength(2)
    expect(result[0]).toEqual({ label: 'Remote Config', variant: 'named' })
    expect(result[1]).toEqual({ label: 'Health', variant: 'named' })
  })

  it('returns Remote Config, Health, and hex 0x8000 for 0x8006', () => {
    const result = decodeCapabilities(0x8006)
    expect(result).toHaveLength(3)
    expect(result.find(c => c.label === 'Remote Config')).toBeTruthy()
    expect(result.find(c => c.label === 'Health')).toBeTruthy()
    const hexChip = result.find(c => c.variant === 'hex')
    expect(hexChip).toBeTruthy()
    expect(hexChip?.label).toBe('0x8000')
  })

  it('returns only Remote Config for capabilities=2', () => {
    const result = decodeCapabilities(2)
    expect(result).toHaveLength(1)
    expect(result[0]).toEqual({ label: 'Remote Config', variant: 'named' })
  })

  it('returns 8 named chips + 1 hex chip for 0x01FF (all known bits + unknown bit 0x0001)', () => {
    const result = decodeCapabilities(0x01FF)
    const named = result.filter(c => c.variant === 'named')
    const hex = result.filter(c => c.variant === 'hex')
    expect(named).toHaveLength(8)
    expect(hex).toHaveLength(1)
    expect(hex[0].label).toBe('0x1')
  })
})

describe('CapabilityChipList', () => {
  it('renders a container with role="list"', () => {
    const { container } = render(<CapabilityChipList capabilities={6} />)
    const list = container.querySelector('[role="list"]')
    expect(list).toBeTruthy()
  })

  it('has aria-label starting with "Capabilities:"', () => {
    const { container } = render(<CapabilityChipList capabilities={6} />)
    const list = container.querySelector('[role="list"]')
    expect(list?.getAttribute('aria-label')).toMatch(/^Capabilities:/)
  })

  it('renders "Remote Config" and "Health" chips for capabilities=6', () => {
    render(<CapabilityChipList capabilities={6} />)
    expect(screen.getByText('Remote Config')).toBeTruthy()
    expect(screen.getByText('Health')).toBeTruthy()
  })

  it('renders "None" chip for capabilities=0', () => {
    render(<CapabilityChipList capabilities={0} />)
    expect(screen.getByText('None')).toBeTruthy()
  })

  it('renders "Remote Config", "Health", and "0x8000" for capabilities=0x8006', () => {
    render(<CapabilityChipList capabilities={0x8006} />)
    expect(screen.getByText('Remote Config')).toBeTruthy()
    expect(screen.getByText('Health')).toBeTruthy()
    expect(screen.getByText('0x8000')).toBeTruthy()
  })

  it('renders hex chip with title for unknown bit 0x8000', () => {
    const { container } = render(<CapabilityChipList capabilities={0x8000} />)
    const hexChip = container.querySelector('[title="Unknown capability bit: 0x8000"]')
    expect(hexChip).toBeTruthy()
  })

  it('renders only "Remote Config" chip for capabilities=2', () => {
    const { container } = render(<CapabilityChipList capabilities={2} />)
    const items = container.querySelectorAll('[role="listitem"]')
    expect(items).toHaveLength(1)
    expect(screen.getByText('Remote Config')).toBeTruthy()
  })
})

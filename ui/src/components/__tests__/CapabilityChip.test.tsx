import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { CapabilityChip } from '../CapabilityChip'

describe('CapabilityChip', () => {
  describe('named variant', () => {
    it('renders the label text', () => {
      render(<CapabilityChip label="Remote Config" variant="named" />)
      expect(screen.getByText('Remote Config')).toBeTruthy()
    })

    it('has role="listitem"', () => {
      const { container } = render(<CapabilityChip label="Remote Config" variant="named" />)
      const chip = container.querySelector('[role="listitem"]')
      expect(chip).toBeTruthy()
    })

    it('includes named variant color classes', () => {
      const { container } = render(<CapabilityChip label="Remote Config" variant="named" />)
      const chip = container.querySelector('[role="listitem"]')
      expect(chip?.className).toContain('border-[#1e2d6b]')
      expect(chip?.className).toContain('bg-[#162050]')
      expect(chip?.className).toContain('text-[#7b93e8]')
    })

    it('does not have a title attribute', () => {
      const { container } = render(<CapabilityChip label="Remote Config" variant="named" />)
      const chip = container.querySelector('[role="listitem"]')
      expect(chip?.hasAttribute('title')).toBe(false)
    })
  })

  describe('hex variant', () => {
    it('renders the label text', () => {
      render(<CapabilityChip label="0x8000" variant="hex" />)
      expect(screen.getByText('0x8000')).toBeTruthy()
    })

    it('has role="listitem"', () => {
      const { container } = render(<CapabilityChip label="0x8000" variant="hex" />)
      const chip = container.querySelector('[role="listitem"]')
      expect(chip).toBeTruthy()
    })

    it('includes hex variant color classes', () => {
      const { container } = render(<CapabilityChip label="0x8000" variant="hex" />)
      const chip = container.querySelector('[role="listitem"]')
      expect(chip?.className).toContain('border-border')
      expect(chip?.className).toContain('bg-card')
      expect(chip?.className).toContain('text-foreground-muted')
      expect(chip?.className).toContain('font-mono')
    })

    it('has title="Unknown capability bit: {label}"', () => {
      const { container } = render(<CapabilityChip label="0x8000" variant="hex" />)
      const chip = container.querySelector('[role="listitem"]')
      expect(chip?.getAttribute('title')).toBe('Unknown capability bit: 0x8000')
    })

    it('renders None chip with hex variant without title', () => {
      const { container } = render(<CapabilityChip label="None" variant="hex" />)
      const chip = container.querySelector('[role="listitem"]')
      expect(chip?.getAttribute('title')).toBe('Unknown capability bit: None')
    })
  })
})

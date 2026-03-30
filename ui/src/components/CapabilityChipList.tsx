import { CapabilityChip } from './CapabilityChip'

const CAPABILITY_BITS: ReadonlyArray<{ bit: number; label: string }> = [
  { bit: 0x0002, label: 'Remote Config' },
  { bit: 0x0004, label: 'Health' },
  { bit: 0x0008, label: 'Packages Available' },
  { bit: 0x0010, label: 'Upgrade Targets' },
  { bit: 0x0020, label: 'Package Updates' },
  { bit: 0x0040, label: 'Connection Settings' },
  { bit: 0x0080, label: 'Connection Settings Offers' },
  { bit: 0x0100, label: 'Live Metrics' },
] as const

export function decodeCapabilities(
  capabilities: number,
): Array<{ label: string; variant: 'named' | 'hex' }> {
  if (capabilities === 0) {
    return [{ label: 'None', variant: 'hex' }]
  }

  const chips: Array<{ label: string; variant: 'named' | 'hex' }> = []
  let remaining = capabilities

  for (const { bit, label } of CAPABILITY_BITS) {
    if (remaining & bit) {
      chips.push({ label, variant: 'named' })
      remaining &= ~bit
    }
  }

  let unknownBit = 1
  let rest = remaining
  while (rest !== 0) {
    if (rest & 1) {
      chips.push({
        label: `0x${unknownBit.toString(16)}`,
        variant: 'hex',
      })
    }
    rest >>>= 1
    unknownBit <<= 1
  }

  return chips
}

export function CapabilityChipList({ capabilities }: { capabilities: number }) {
  const chips = decodeCapabilities(capabilities)

  return (
    <span
      role="list"
      aria-label={`Capabilities: ${chips.map(c => c.label).join(', ')}`}
      className="flex flex-wrap gap-1.5"
    >
      {chips.map(chip => (
        <CapabilityChip key={`${chip.variant}-${chip.label}`} label={chip.label} variant={chip.variant} />
      ))}
    </span>
  )
}

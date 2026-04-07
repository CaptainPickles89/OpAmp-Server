import { CapabilityChip } from './CapabilityChip'

// Bit definitions sourced directly from proto/opamp.proto AgentCapabilities enum
const CAPABILITY_BITS: ReadonlyArray<{ bit: number; label: string; description: string }> = [
  { bit: 0x0001, label: 'Reports Status',                    description: 'Sends status updates to the server' },
  { bit: 0x0002, label: 'Accepts Remote Config',             description: 'Can receive and apply config from the server' },
  { bit: 0x0004, label: 'Reports Effective Config',          description: 'Sends its active running config to the server' },
  { bit: 0x0008, label: 'Accepts Packages',                  description: 'Can receive and install packages' },
  { bit: 0x0010, label: 'Reports Package Statuses',          description: 'Reports status of installed packages' },
  { bit: 0x0020, label: 'Reports Own Traces',                description: 'Sends its own telemetry traces' },
  { bit: 0x0040, label: 'Reports Own Metrics',               description: 'Sends its own telemetry metrics' },
  { bit: 0x0080, label: 'Reports Own Logs',                  description: 'Sends its own telemetry logs' },
  { bit: 0x0100, label: 'Accepts OpAMP Connection Settings', description: 'Can reconfigure its OpAMP connection' },
  { bit: 0x0200, label: 'Accepts Other Connection Settings', description: 'Can reconfigure other connections (e.g. exporters)' },
  { bit: 0x0400, label: 'Accepts Restart Command',           description: 'Can be restarted by the server' },
  { bit: 0x0800, label: 'Reports Health',                    description: 'Sends health status to the server' },
  { bit: 0x1000, label: 'Reports Remote Config',             description: 'Echoes back applied remote config' },
  { bit: 0x2000, label: 'Reports Heartbeat',                 description: 'Sends periodic heartbeat messages' },
  { bit: 0x4000, label: 'Reports Available Components',      description: 'Advertises which components are available' },
  { bit: 0x8000, label: 'Reports Connection Settings Status', description: 'Reports status of connection settings changes' },
] as const

export function decodeCapabilities(
  capabilities: number,
): Array<{ label: string; description: string; variant: 'named' | 'hex' }> {
  if (capabilities === 0) {
    return [{ label: 'None', description: '', variant: 'hex' }]
  }

  const chips: Array<{ label: string; description: string; variant: 'named' | 'hex' }> = []
  let remaining = capabilities

  for (const { bit, label, description } of CAPABILITY_BITS) {
    if (remaining & bit) {
      chips.push({ label, description, variant: 'named' })
      remaining &= ~bit
    }
  }

  // Any bits not in the known map fall back to hex display
  let unknownBit = 1
  let rest = remaining
  while (rest !== 0) {
    if (rest & 1) {
      chips.push({
        label: `0x${unknownBit.toString(16).toUpperCase()}`,
        description: 'Unknown capability',
        variant: 'hex',
      })
    }
    rest >>>= 1
    unknownBit <<= 1
  }

  return chips
}

export function CapabilityChipList({ capabilities, showDescriptions = true }: { capabilities: number; showDescriptions?: boolean }) {
  const chips = decodeCapabilities(capabilities)

  return (
    <div
      role="list"
      aria-label={`Capabilities: ${chips.map(c => c.label).join(', ')}`}
      className={showDescriptions ? 'flex flex-col gap-1.5' : 'flex flex-wrap gap-1.5'}
    >
      {chips.map(chip => (
        <div key={`${chip.variant}-${chip.label}`} role="listitem" className={showDescriptions ? 'flex flex-col' : undefined}>
          <CapabilityChip label={chip.label} variant={chip.variant} />
          {showDescriptions && chip.description && (
            <span className="text-xs text-foreground-subtle mt-0.5 pl-0.5">{chip.description}</span>
          )}
        </div>
      ))}
    </div>
  )
}

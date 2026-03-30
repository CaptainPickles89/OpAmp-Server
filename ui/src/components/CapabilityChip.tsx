interface CapabilityChipProps {
  label: string
  variant: 'named' | 'hex'
}

export function CapabilityChip({ label, variant }: CapabilityChipProps) {
  const baseClasses = 'inline-flex items-center rounded border px-2 py-1 text-xs font-medium'

  if (variant === 'named') {
    return (
      <span
        role="listitem"
        className={`${baseClasses} border-[#1e2d6b] bg-[#162050] text-[#7b93e8]`}
      >
        {label}
      </span>
    )
  }

  return (
    <span
      role="listitem"
      className={`${baseClasses} border-border bg-card text-foreground-muted font-mono`}
      title={`Unknown capability bit: ${label}`}
    >
      {label}
    </span>
  )
}

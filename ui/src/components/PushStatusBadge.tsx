import type { PushState } from '@/api/types'

interface PushStatusBadgeProps {
  pushState: PushState
}

export function PushStatusBadge({ pushState }: PushStatusBadgeProps) {
  if (pushState === 'IDLE') {
    return null
  }

  const config: Record<
    Exclude<PushState, 'IDLE'>,
    { label: string; colorClass: string; pulsing?: boolean }
  > = {
    PUSH_PENDING: {
      label: 'Push Pending',
      colorClass: 'border-amber-700 bg-amber-950 text-amber-300',
    },
    APPLYING: {
      label: 'Applying...',
      colorClass: 'border-[#1e2d6b] bg-[#162050] text-[#7b93e8]',
      pulsing: true,
    },
    APPLIED: {
      label: 'Applied',
      colorClass: 'border-green-700 bg-green-950 text-green-300',
    },
    FAILED: {
      label: 'Failed',
      colorClass: 'border-red-700 bg-red-950 text-red-300',
    },
  }

  const { label, colorClass, pulsing } = config[pushState as Exclude<PushState, 'IDLE'>]

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded border px-2 py-0.5 text-xs font-medium ${colorClass}`}
      aria-live="polite"
    >
      <span
        className={`h-1.5 w-1.5 rounded-full bg-current ${pulsing ? 'motion-safe:animate-pulse' : ''}`}
        aria-hidden="true"
      />
      {label}
    </span>
  )
}

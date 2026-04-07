import { cn } from '@/lib/utils'
import type { HealthStatus } from '@/api/types'

interface HealthBadgeProps {
  status: HealthStatus
  size?: 'sm' | 'md'
  variant?: 'default' | 'pulse'
}

const statusConfig: Record<HealthStatus, { dot: string; bg: string; ping: string; label: string }> = {
  healthy:   { dot: 'text-green-400',          bg: 'bg-green-400',  ping: 'bg-green-400',  label: 'Healthy' },
  degraded:  { dot: 'text-amber-400',          bg: 'bg-amber-400',  ping: 'bg-amber-400',  label: 'Degraded' },
  unhealthy: { dot: 'text-red-400',            bg: 'bg-red-400',    ping: 'bg-red-400',    label: 'Unhealthy' },
  unknown:   { dot: 'text-foreground-subtle',  bg: 'bg-slate-400',  ping: 'bg-slate-400',  label: 'Unknown' },
}

export function HealthBadge({ status, size = 'sm', variant = 'default' }: HealthBadgeProps) {
  const config = statusConfig[status]

  if (variant === 'pulse') {
    return (
      <span
        className="inline-flex items-center justify-center"
        aria-label={config.label}
        title={config.label}
      >
        <span className="relative flex h-3.5 w-3.5">
          <span
            className={cn(
              'motion-safe:animate-ping absolute inline-flex h-full w-full rounded-full opacity-60',
              config.ping,
            )}
          />
          <span className={cn('relative inline-flex h-3.5 w-3.5 rounded-full', config.bg)} />
        </span>
      </span>
    )
  }

  return (
    <span
      className={cn('inline-flex items-center gap-1.5', size === 'md' ? 'text-sm' : 'text-xs')}
      aria-label={status}
    >
      <svg
        className={cn('shrink-0', size === 'md' ? 'h-2.5 w-2.5' : 'h-2 w-2', config.dot)}
        viewBox="0 0 8 8"
        fill="currentColor"
        aria-hidden="true"
      >
        <circle cx="4" cy="4" r="3" />
      </svg>
      <span className="text-foreground-secondary">{config.label}</span>
    </span>
  )
}

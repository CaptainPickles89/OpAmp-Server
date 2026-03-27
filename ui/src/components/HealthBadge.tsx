import { cn } from '@/lib/utils'
import type { HealthStatus } from '@/api/types'

interface HealthBadgeProps {
  status: HealthStatus
  size?: 'sm' | 'md'
}

const statusConfig: Record<HealthStatus, { dot: string; label: string }> = {
  healthy: { dot: 'text-green-400', label: 'Healthy' },
  degraded: { dot: 'text-amber-400', label: 'Degraded' },
  unhealthy: { dot: 'text-red-400', label: 'Unhealthy' },
  unknown: { dot: 'text-slate-400', label: 'Unknown' },
}

export function HealthBadge({ status, size = 'sm' }: HealthBadgeProps) {
  const config = statusConfig[status]

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
      <span className="text-slate-300">{config.label}</span>
    </span>
  )
}

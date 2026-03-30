import type { Stats } from '@/api/types'

interface AgentHealthStatProps {
  stats: Stats
}

export function AgentHealthStat({ stats }: AgentHealthStatProps) {
  const { healthy_count, total_count } = stats
  return (
    <div className="mx-auto w-fit min-w-[240px] rounded-xl border border-border bg-card p-6 shadow-[0_0_16px_rgba(66,92,199,0.2)]">
      <p className="text-center">
        <span
          className="text-4xl font-semibold text-healthy"
          aria-live="polite"
        >
          {healthy_count} of {total_count}
        </span>
      </p>
      <p className="mt-1 text-center text-xs font-medium text-foreground-muted">
        agents healthy
      </p>
    </div>
  )
}

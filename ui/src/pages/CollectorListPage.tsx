import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCollectors } from '@/hooks/useCollectors'
import { HealthBadge } from '@/components/HealthBadge'
import { RelativeTime } from '@/components/RelativeTime'
import type { HealthStatus } from '@/api/types'

const HEALTH_FILTERS: Array<{ value: HealthStatus | 'all'; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'healthy', label: 'Healthy' },
  { value: 'degraded', label: 'Degraded' },
  { value: 'unhealthy', label: 'Unhealthy' },
  { value: 'unknown', label: 'Unknown' },
]

function truncateUid(uid: string): string {
  if (uid.length <= 12) return uid
  return `${uid.slice(0, 8)}...${uid.slice(-4)}`
}

function CollectorTableSkeleton() {
  return (
    <div className="rounded-lg border border-slate-800 overflow-hidden" aria-label="Loading collectors">
      {Array.from({ length: 5 }, (_, i) => (
        <div key={i} className="flex items-center gap-4 px-4 py-3 border-b border-slate-800 last:border-b-0">
          <div className="h-4 w-48 animate-pulse rounded bg-slate-700" />
          <div className="h-4 w-20 animate-pulse rounded bg-slate-700" />
          <div className="h-4 w-24 animate-pulse rounded bg-slate-700" />
          <div className="h-4 w-12 animate-pulse rounded bg-slate-700" />
        </div>
      ))}
    </div>
  )
}

export function CollectorListPage() {
  const navigate = useNavigate()
  const { data, isLoading, isError, isFetching, refetch } = useCollectors()
  const [search, setSearch] = useState('')
  const [healthFilter, setHealthFilter] = useState<HealthStatus | 'all'>('all')

  const filtered = (data ?? []).filter(c => {
    const matchSearch = c.instance_uid.toLowerCase().includes(search.toLowerCase())
    const matchHealth = healthFilter === 'all' || c.health_status === healthFilter
    return matchSearch && matchHealth
  })

  const hasActiveFilters = search !== '' || healthFilter !== 'all'

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-100">Collectors</h1>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          {isFetching && (
            <svg
              className="h-3 w-3 animate-spin"
              viewBox="0 0 24 24"
              fill="none"
              aria-label="Refreshing"
            >
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          )}
          <span>Refreshes every 5s</span>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="search"
          placeholder="Filter by UID..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="rounded-md border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500 w-64"
          aria-label="Search collectors by UID"
        />
        <div className="flex gap-1" role="group" aria-label="Filter by health status">
          {HEALTH_FILTERS.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setHealthFilter(value)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                healthFilter === value
                  ? 'bg-slate-600 text-slate-100'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {isLoading && <CollectorTableSkeleton />}

      {isError && (
        <div className="rounded-lg border border-slate-800 p-8 text-center">
          <p className="text-slate-300 font-medium">Failed to load collectors.</p>
          <p className="text-slate-500 text-sm mt-1">Check that the server is running and try again.</p>
          <button
            onClick={() => void refetch()}
            className="mt-4 rounded-md bg-slate-700 px-4 py-2 text-sm text-slate-100 hover:bg-slate-600 transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {!isLoading && !isError && data?.length === 0 && (
        <div className="rounded-lg border border-slate-800 p-8 text-center">
          <p className="text-slate-300 font-medium">No collectors connected.</p>
          <p className="text-slate-500 text-sm mt-1">
            See{' '}
            <a href="/getting-started" className="text-slate-300 underline hover:text-white">
              Getting Started
            </a>{' '}
            to connect your first collector.
          </p>
        </div>
      )}

      {!isLoading && !isError && data && data.length > 0 && filtered.length === 0 && hasActiveFilters && (
        <div className="rounded-lg border border-slate-800 p-8 text-center">
          <p className="text-slate-300 font-medium">No collectors match your filters.</p>
          <button
            onClick={() => { setSearch(''); setHealthFilter('all') }}
            className="mt-3 rounded-md bg-slate-700 px-4 py-2 text-sm text-slate-100 hover:bg-slate-600 transition-colors"
          >
            Clear filters
          </button>
        </div>
      )}

      {!isLoading && !isError && filtered.length > 0 && (
        <div className="rounded-lg border border-slate-800 overflow-hidden">
          {/* Table header */}
          <div className="grid grid-cols-4 gap-4 px-4 py-2 bg-slate-800/50 text-xs font-medium text-slate-400 uppercase tracking-wider">
            <span>Instance UID</span>
            <span>Health</span>
            <span>Last Seen</span>
            <span>Capabilities</span>
          </div>
          {/* Rows */}
          {filtered.map(collector => (
            <div
              key={collector.instance_uid}
              role="row"
              onClick={() => navigate(`/collectors/${collector.instance_uid}`)}
              className="grid grid-cols-4 gap-4 px-4 py-3 border-t border-slate-800 cursor-pointer hover:bg-slate-800/50 transition-colors items-center"
            >
              <span
                className="font-mono text-sm text-slate-300 truncate"
                title={collector.instance_uid}
              >
                {truncateUid(collector.instance_uid)}
              </span>
              <span>
                <HealthBadge status={collector.health_status} size="sm" />
              </span>
              <span className="text-sm text-slate-400">
                <RelativeTime nanoseconds={collector.last_seen} />
              </span>
              <span className="text-sm text-slate-400 font-mono">{collector.capabilities}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

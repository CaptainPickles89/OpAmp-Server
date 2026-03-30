import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCollectors } from '@/hooks/useCollectors'
import { useResourceAttrKeys } from '@/hooks/useResourceAttrKeys'
import { useColumnPrefs } from '@/hooks/useColumnPrefs'
import { ColumnPicker } from '@/components/ColumnPicker'
import { HealthBadge } from '@/components/HealthBadge'
import { RelativeTime } from '@/components/RelativeTime'
import { CapabilityChipList } from '@/components/CapabilityChipList'
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
    <div className="rounded-lg border border-border overflow-hidden" aria-label="Loading collectors">
      {Array.from({ length: 5 }, (_, i) => (
        <div key={i} className="flex items-center gap-4 px-4 py-3 border-b border-border last:border-b-0">
          <div className="h-4 w-48 animate-pulse rounded bg-skeleton" />
          <div className="h-4 w-20 animate-pulse rounded bg-skeleton" />
          <div className="h-4 w-24 animate-pulse rounded bg-skeleton" />
          <div className="h-4 w-12 animate-pulse rounded bg-skeleton" />
        </div>
      ))}
    </div>
  )
}

export function CollectorListPage() {
  const navigate = useNavigate()
  const { data, isLoading, isError, isFetching, refetch } = useCollectors()
  const { data: attrKeys } = useResourceAttrKeys()
  const { enabledKeys, toggleKey } = useColumnPrefs()
  const [search, setSearch] = useState('')
  const [healthFilter, setHealthFilter] = useState<HealthStatus | 'all'>('all')

  const totalCols = 4 + enabledKeys.length
  const gridStyle = { gridTemplateColumns: `repeat(${totalCols}, minmax(120px, 1fr))` }

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
        <h1 className="text-2xl font-semibold text-foreground">Collectors</h1>
        <div className="flex items-center gap-2 text-xs text-foreground-subtle">
          <ColumnPicker
            allKeys={attrKeys ?? []}
            enabledKeys={enabledKeys}
            onToggle={toggleKey}
          />
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
          className="rounded-full border border-border-accent bg-card px-4 py-1.5 text-sm text-foreground placeholder-foreground-subtle focus:outline-none focus:ring-1 focus:ring-otel-blue w-64"
          aria-label="Search collectors by UID"
        />
        <div
          className="flex items-center gap-1 rounded-full bg-nav-pill border border-border-accent/40 px-1.5 py-1"
          role="group"
          aria-label="Filter by health status"
        >
          {HEALTH_FILTERS.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setHealthFilter(value)}
              className={`rounded-full px-3 py-0.5 text-xs font-medium transition-all duration-200 ${
                healthFilter === value
                  ? 'bg-otel-blue text-white shadow-[0_0_8px_rgba(66,92,199,0.35)]'
                  : 'text-foreground-muted hover:text-foreground hover:bg-hover'
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
        <div className="rounded-lg border border-border p-8 text-center">
          <p className="text-foreground-secondary font-medium">Failed to load collectors.</p>
          <p className="text-foreground-subtle text-sm mt-1">Check that the server is running and try again.</p>
          <button
            onClick={() => void refetch()}
            className="mt-4 rounded-full bg-otel-blue px-5 py-2 text-sm text-white hover:bg-otel-blue-hover transition-colors shadow-[0_0_10px_rgba(66,92,199,0.3)]"
          >
            Retry
          </button>
        </div>
      )}

      {!isLoading && !isError && data?.length === 0 && (
        <div className="rounded-lg border border-border p-8 text-center">
          <p className="text-foreground-secondary font-medium">No collectors connected.</p>
          <p className="text-foreground-subtle text-sm mt-1">
            See{' '}
            <a href="/getting-started" className="text-otel-amber hover:text-amber-300 transition-colors">
              Getting Started
            </a>{' '}
            to connect your first collector.
          </p>
        </div>
      )}

      {!isLoading && !isError && data && data.length > 0 && filtered.length === 0 && hasActiveFilters && (
        <div className="rounded-lg border border-border p-8 text-center">
          <p className="text-foreground-secondary font-medium">No collectors match your filters.</p>
          <button
            onClick={() => { setSearch(''); setHealthFilter('all') }}
            className="mt-3 rounded-full bg-otel-blue px-5 py-2 text-sm text-white hover:bg-otel-blue-hover transition-colors"
          >
            Clear filters
          </button>
        </div>
      )}

      {!isLoading && !isError && filtered.length > 0 && (
        <div className="rounded-lg border border-border overflow-hidden">
          {/* Table header */}
          <div
            className="grid gap-4 px-4 py-2.5 bg-card text-xs font-medium text-foreground-subtle uppercase tracking-widest border-b border-border"
            style={gridStyle}
          >
            <span className="text-center">Instance UID</span>
            <span className="text-center">Health</span>
            <span className="text-center">Last Seen</span>
            <span className="text-center">Capabilities</span>
            {enabledKeys.map(key => (
              <span key={key} className="text-center">{key}</span>
            ))}
          </div>
          {/* Rows */}
          {filtered.map(collector => (
            <div
              key={collector.instance_uid}
              role="row"
              onClick={() => navigate(`/collectors/${collector.instance_uid}`)}
              className="grid gap-4 px-4 py-3 border-t border-border cursor-pointer hover:bg-hover transition-colors items-center group"
              style={gridStyle}
            >
              <span
                className="font-mono text-sm text-foreground-secondary group-hover:text-foreground truncate text-center transition-colors"
                title={collector.instance_uid}
              >
                {truncateUid(collector.instance_uid)}
              </span>
              <span className="flex justify-center">
                <HealthBadge status={collector.health_status} variant="pulse" />
              </span>
              <span className="text-sm text-foreground-subtle text-center">
                <RelativeTime nanoseconds={collector.last_seen} />
              </span>
              <span className="flex justify-center">
                <CapabilityChipList capabilities={collector.capabilities} />
              </span>
              {enabledKeys.map(key => (
                <span key={key} className="text-sm text-center truncate">
                  {collector.resource_attributes[key] ?? (
                    <span className="text-foreground-subtle" aria-label="not available">{'\u2014'}</span>
                  )}
                </span>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

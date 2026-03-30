import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useCollector, usePushConfig } from '@/hooks/useCollector'
import { HealthBadge } from '@/components/HealthBadge'
import { RelativeTime } from '@/components/RelativeTime'
import { PushStatusBadge } from '@/components/PushStatusBadge'
import { ConfigEditor } from '@/components/ConfigEditor'
import { CapabilityChipList } from '@/components/CapabilityChipList'
import { extractYaml } from '@/api/types'
import type { HealthSnapshot } from '@/api/types'
import { ApiError } from '@/api/client'

function HealthSnapshotRow({ snapshot }: { snapshot: HealthSnapshot }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-border last:border-b-0 text-sm">
      <span className="text-foreground-muted">
        <RelativeTime nanoseconds={snapshot.recorded_at} />
      </span>
      <span className={snapshot.healthy ? 'text-green-400' : 'text-red-400'}>
        {snapshot.healthy ? 'Healthy' : 'Unhealthy'}
      </span>
      {snapshot.last_error && (
        <span className="text-red-400 text-xs truncate max-w-[200px]" title={snapshot.last_error}>
          {snapshot.last_error}
        </span>
      )}
    </div>
  )
}

function DetailSkeleton() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6" aria-label="Loading collector details">
      {[0, 1].map(i => (
        <div key={i} className="rounded-lg border border-border p-4 space-y-3">
          <div className="h-5 w-32 animate-pulse rounded bg-skeleton" />
          <div className="h-4 w-full animate-pulse rounded bg-skeleton" />
          <div className="h-4 w-3/4 animate-pulse rounded bg-skeleton" />
          <div className="h-64 animate-pulse rounded bg-skeleton" />
        </div>
      ))}
    </div>
  )
}

export function CollectorDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: collector, isLoading, isError, error } = useCollector(id ?? '')
  const mutation = usePushConfig(id ?? '')

  const [isEditMode, setIsEditMode] = useState(false)
  const [editedYaml, setEditedYaml] = useState('')
  const [conflictError, setConflictError] = useState<string | null>(null)
  const [applyingStart, setApplyingStart] = useState<number | null>(null)
  const [showTimeoutWarning, setShowTimeoutWarning] = useState(false)

  // Track APPLYING start time for timeout warning
  useEffect(() => {
    if (collector?.push_status.push_state === 'APPLYING') {
      if (applyingStart === null) setApplyingStart(Date.now())
    } else {
      setApplyingStart(null)
      setShowTimeoutWarning(false)
    }
  }, [collector?.push_status.push_state, applyingStart])

  useEffect(() => {
    if (applyingStart === null) return
    const timeout = setTimeout(() => {
      setShowTimeoutWarning(true)
    }, 30_000)
    return () => clearTimeout(timeout)
  }, [applyingStart])

  function handleEditStart() {
    setEditedYaml(extractYaml(collector?.effective_config ?? null))
    setConflictError(null)
    setIsEditMode(true)
  }

  function handleCancel() {
    setIsEditMode(false)
    setEditedYaml(extractYaml(collector?.effective_config ?? null))
    setConflictError(null)
  }

  async function handlePush() {
    try {
      await mutation.mutateAsync(editedYaml)
      setIsEditMode(false)
      setConflictError(null)
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setConflictError('A config push is already in progress. Wait for it to complete.')
      }
    }
  }

  if (isLoading) return <DetailSkeleton />

  if (isError) {
    const is404 = error instanceof ApiError && error.status === 404
    if (is404) {
      return (
        <div className="rounded-lg border border-border p-8 text-center">
          <p className="text-foreground-secondary font-medium">Collector not found.</p>
          <Link to="/collectors" className="mt-4 inline-block text-sm text-otel-blue hover:text-blue-300 transition-colors">
            Back to collectors
          </Link>
        </div>
      )
    }
    return (
      <div className="rounded-lg border border-border p-8 text-center">
        <p className="text-foreground-secondary font-medium">Failed to load collector details.</p>
      </div>
    )
  }

  if (!collector) return null

  const effectiveYaml = extractYaml(collector.effective_config)

  return (
    <div className="space-y-4">
      {/* Back link */}
      <Link to="/collectors" className="inline-flex items-center gap-1.5 text-sm text-foreground-subtle hover:text-otel-blue transition-colors">
        <span aria-hidden="true">←</span> Collectors
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Health Panel */}
        <div className="rounded-lg border border-border bg-card p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">Health</h2>
            <HealthBadge status={collector.health_status} size="md" />
          </div>

          <dl className="space-y-2 text-sm">
            <div className="flex flex-col">
              <dt className="text-foreground-muted">Instance UID</dt>
              <dd className="font-mono text-foreground-secondary break-all">{collector.instance_uid}</dd>
            </div>
            <div className="flex flex-col">
              <dt className="text-foreground-muted">First Seen</dt>
              <dd className="text-foreground-secondary"><RelativeTime nanoseconds={collector.first_seen} /></dd>
            </div>
            <div className="flex flex-col">
              <dt className="text-foreground-muted">Last Seen</dt>
              <dd className="text-foreground-secondary"><RelativeTime nanoseconds={collector.last_seen} /></dd>
            </div>
            <div className="flex flex-col">
              <dt className="text-foreground-muted">Capabilities</dt>
              <dd><CapabilityChipList capabilities={collector.capabilities} /></dd>
            </div>
          </dl>

          {collector.health_history.length > 0 && (
            <div>
              <h3 className="text-xs font-medium text-foreground-subtle uppercase tracking-wider mb-2">Health History</h3>
              <div className="rounded border border-border">
                {collector.health_history.map(snapshot => (
                  <HealthSnapshotRow key={snapshot.recorded_at} snapshot={snapshot} />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: Config Panel */}
        <div className="rounded-lg border border-border bg-card p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">Effective Config</h2>
            <PushStatusBadge pushState={collector.push_status.push_state} />
          </div>

          {!collector.effective_config && (
            <p className="text-foreground-subtle text-sm italic">No config reported yet.</p>
          )}

          <ConfigEditor
            value={isEditMode ? editedYaml : (effectiveYaml || '')}
            onChange={isEditMode ? setEditedYaml : undefined}
            readOnly={!isEditMode}
          />

          {/* Timeout warning */}
          {showTimeoutWarning && (
            <div className="rounded border border-amber-700 bg-amber-950 p-3">
              <p className="text-amber-300 text-sm">
                Push is taking longer than expected. The collector may be offline.
              </p>
            </div>
          )}

          {/* Conflict error */}
          {conflictError && (
            <div role="alert" className="rounded border border-red-800 bg-red-950 p-3">
              <p className="text-red-400 text-sm">{conflictError}</p>
            </div>
          )}

          {/* FAILED callout */}
          {collector.push_status.push_state === 'FAILED' && (
            <div role="alert" className="rounded border border-red-800 bg-red-950 p-4">
              <p className="text-red-400 font-semibold">Config push failed</p>
              <p className="text-sm text-foreground-secondary mt-1">
                The server has automatically rolled back to the previous config.
              </p>
            </div>
          )}

          {/* APPLIED success callout */}
          {collector.push_status.push_state === 'APPLIED' && (
            <div role="status" className="rounded border border-green-800 bg-green-950 p-4">
              <p className="text-green-400 font-semibold">Config successfully applied</p>
            </div>
          )}

          {/* Edit controls */}
          {!isEditMode ? (
            <button
              onClick={handleEditStart}
              className="rounded-full bg-otel-blue px-5 py-2 text-sm text-white hover:bg-otel-blue-hover transition-colors shadow-[0_0_10px_rgba(66,92,199,0.3)]"
            >
              Edit &amp; Push
            </button>
          ) : (
            <div className="flex gap-2">
              <button
                onClick={() => void handlePush()}
                disabled={mutation.isPending}
                className="rounded-full bg-otel-blue px-5 py-2 text-sm text-white hover:bg-otel-blue-hover disabled:opacity-50 transition-colors shadow-[0_0_10px_rgba(66,92,199,0.3)]"
              >
                {mutation.isPending ? 'Pushing...' : 'Push Config'}
              </button>
              <button
                onClick={handleCancel}
                disabled={mutation.isPending}
                className="rounded-full border border-border-accent px-5 py-2 text-sm text-foreground-muted hover:bg-hover hover:text-foreground disabled:opacity-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

import { Link } from 'react-router-dom'
import { useStats } from '@/hooks/useStats'
import { AgentHealthStat } from '@/components/AgentHealthStat'

// Official OpenTelemetry icon — paths sourced from docs/OpenTelemetry.svg
function OtelTelescopeIcon({ className }: { className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" aria-hidden="true" className={className}>
      <path
        fill="#f5a800"
        d="M67.648 69.797c-5.246 5.25-5.246 13.758 0 19.008 5.25 5.246 13.758 5.246 19.004 0 5.25-5.25 5.25-13.758 0-19.008-5.246-5.246-13.754-5.246-19.004 0Zm14.207 14.219a6.649 6.649 0 0 1-9.41 0 6.65 6.65 0 0 1 0-9.407 6.649 6.649 0 0 1 9.41 0c2.598 2.586 2.598 6.809 0 9.407ZM86.43 3.672l-8.235 8.234a4.17 4.17 0 0 0 0 5.875l32.149 32.149a4.17 4.17 0 0 0 5.875 0l8.234-8.235c1.61-1.61 1.61-4.261 0-5.87L92.29 3.671a4.159 4.159 0 0 0-5.86 0ZM28.738 108.895a3.763 3.763 0 0 0 0-5.31l-4.183-4.187a3.768 3.768 0 0 0-5.313 0l-8.644 8.649-.016.012-2.371-2.375c-1.313-1.313-3.45-1.313-4.75 0-1.313 1.312-1.313 3.449 0 4.75l14.246 14.242a3.353 3.353 0 0 0 4.746 0c1.3-1.313 1.313-3.45 0-4.746l-2.375-2.375.016-.012Zm0 0"
      />
      <path
        fill="#425cc7"
        d="M72.297 27.313 54.004 45.605c-1.625 1.625-1.625 4.301 0 5.926L65.3 62.824c7.984-5.746 19.18-5.035 26.363 2.153l9.148-9.149c1.622-1.625 1.622-4.297 0-5.922L78.22 27.313a4.185 4.185 0 0 0-5.922 0ZM60.55 67.585l-6.672-6.672c-1.563-1.562-4.125-1.562-5.684 0l-23.53 23.54a4.036 4.036 0 0 0 0 5.687l13.331 13.332a4.036 4.036 0 0 0 5.688 0l15.132-15.157c-3.199-6.609-2.625-14.593 1.735-20.73Zm0 0"
      />
    </svg>
  )
}

export function StatusPage() {
  const { data, isLoading, isError, isFetching } = useStats()

  return (
    <div>
      {/* Hero section with gradient */}
      <section
        className="rounded-2xl py-12 text-center"
        style={{
          background: 'linear-gradient(135deg, var(--color-otel-blue-subtle) 0%, var(--color-background) 60%)',
        }}
      >
        {/* OTel icon in white circle */}
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-white shadow-[0_0_12px_rgba(66,92,199,0.2)] border border-otel-blue/15">
          <OtelTelescopeIcon className="h-7 w-7" />
        </div>

        {/* Heading (STATUS-01) */}
        <h1 className="mt-4 text-4xl font-semibold text-foreground">
          OpAMP Server
        </h1>

        {/* Description (STATUS-02) */}
        <p className="mx-auto mt-3 max-w-prose text-sm text-foreground-muted">
          A management interface for OpenTelemetry Collector fleets. Monitor agent health and push configuration changes from your browser.
        </p>
      </section>

      {/* Stats section */}
      <section className="mt-8">
        {/* Loading state */}
        {isLoading && (
          <div className="mx-auto w-fit min-w-[240px] rounded-xl border border-border bg-card p-6" aria-label="Loading agent stats">
            <div className="mx-auto h-10 w-32 animate-pulse rounded bg-skeleton" />
            <div className="mx-auto mt-2 h-4 w-24 animate-pulse rounded bg-skeleton" />
          </div>
        )}

        {/* Error state */}
        {isError && (
          <div className="rounded-lg border border-border p-8 text-center">
            <p className="text-foreground-secondary font-medium">Could not load agent stats.</p>
            <p className="text-foreground-subtle text-sm mt-1">Check that the server is running and try again.</p>
          </div>
        )}

        {/* Stat card (STATUS-03) */}
        {!isLoading && !isError && data && (
          <>
            <AgentHealthStat stats={data} />
            {/* Empty state sub-text */}
            {data.total_count === 0 && (
              <p className="mt-3 text-center text-sm text-foreground-muted">
                No collectors connected. See{' '}
                <Link to="/getting-started" className="text-otel-amber hover:text-amber-300 transition-colors">
                  Getting Started
                </Link>{' '}
                to connect your first collector.
              </p>
            )}
          </>
        )}

        {/* Refresh indicator */}
        <div className="mt-4 flex items-center justify-center gap-2 text-xs text-foreground-subtle">
          {isFetching && (
            <svg className="h-3 w-3 animate-spin" viewBox="0 0 24 24" fill="none" aria-label="Refreshing">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          )}
          <span>Refreshes every 5s</span>
        </div>
      </section>
    </div>
  )
}

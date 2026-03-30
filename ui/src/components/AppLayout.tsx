import type { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Moon, Sun } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useTheme } from '@/hooks/useTheme'

interface AppLayoutProps {
  children: ReactNode
}

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

export function AppLayout({ children }: AppLayoutProps) {
  const location = useLocation()
  const { theme, toggleTheme } = useTheme()

  const navLinks = [
    { to: '/', label: 'Status' },
    { to: '/collectors', label: 'Collectors' },
    { to: '/getting-started', label: 'Getting Started' },
  ]

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border bg-header">
        {/* Thin OTel-blue accent line */}
        <div className="h-0.5 bg-gradient-to-r from-otel-blue via-[#5b72d6] to-transparent" />
        <nav className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-14 items-center gap-6">

            {/* Brand */}
            <Link to="/" className="flex items-center gap-2.5 shrink-0 group">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-white shadow-[0_0_12px_rgba(66,92,199,0.2)] border border-otel-blue/15 shrink-0">
                <OtelTelescopeIcon className="h-5 w-5" />
              </span>
              <span className="text-sm font-semibold tracking-wide text-foreground group-hover:text-foreground transition-colors">
                OpAMP<span className="text-otel-amber"> Server</span>
              </span>
            </Link>

            {/* Divider */}
            <div className="h-5 w-px bg-border shrink-0" />

            {/* Pill nav */}
            <div className="flex items-center gap-1.5 rounded-full bg-nav-pill border border-border-accent/40 px-1.5 py-1">
              {navLinks.map(({ to, label }) => (
                <Link
                  key={to}
                  to={to}
                  className={cn(
                    'rounded-full px-4 py-1 text-sm font-medium transition-all duration-200',
                    location.pathname === to
                      ? 'bg-otel-blue text-white shadow-[0_0_10px_rgba(66,92,199,0.4)]'
                      : 'text-foreground-muted hover:text-foreground hover:bg-hover',
                  )}
                >
                  {label}
                </Link>
              ))}
            </div>

            {/* Spacer */}
            <div className="ml-auto" />

            {/* Theme toggle */}
            <button
              onClick={toggleTheme}
              aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              className="rounded-full p-2 text-foreground-muted hover:text-foreground hover:bg-hover transition-colors"
            >
              {theme === 'dark'
                ? <Sun className="h-4 w-4" aria-hidden="true" />
                : <Moon className="h-4 w-4" aria-hidden="true" />
              }
            </button>
          </div>
        </nav>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  )
}

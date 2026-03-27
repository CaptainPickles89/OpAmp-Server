import { useState, useEffect } from 'react'

interface RelativeTimeProps {
  nanoseconds: number
}

function formatRelative(ms: number): string {
  const now = Date.now()
  const diffMs = now - ms
  const diffSec = Math.floor(diffMs / 1000)

  const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })

  if (diffSec < 10) {
    return 'just now'
  }
  if (diffSec < 60) {
    return rtf.format(-diffSec, 'second')
  }
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) {
    return rtf.format(-diffMin, 'minute')
  }
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) {
    return rtf.format(-diffHr, 'hour')
  }
  const diffDay = Math.floor(diffHr / 24)
  return rtf.format(-diffDay, 'day')
}

export function RelativeTime({ nanoseconds }: RelativeTimeProps) {
  const ms = nanoseconds / 1_000_000
  const [label, setLabel] = useState(() => formatRelative(ms))
  const isoString = new Date(ms).toISOString()

  useEffect(() => {
    setLabel(formatRelative(ms))
    const interval = setInterval(() => {
      setLabel(formatRelative(ms))
    }, 30_000)
    return () => clearInterval(interval)
  }, [ms])

  return (
    <time dateTime={isoString} title={isoString}>
      {label}
    </time>
  )
}

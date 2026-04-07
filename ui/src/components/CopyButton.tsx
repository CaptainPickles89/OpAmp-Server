import { useState } from 'react'
import { Check, Clipboard } from 'lucide-react'
import { cn } from '@/lib/utils'

interface CopyButtonProps {
  text: string
  label?: string
  className?: string
}

export function CopyButton({ text, label = 'Copy', className }: CopyButtonProps) {
  const [copied, setCopied] = useState(false)
  const clipboardAvailable = typeof navigator !== 'undefined' && 'clipboard' in navigator

  async function handleCopy() {
    if (!clipboardAvailable) return
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Ignore clipboard errors silently
    }
  }

  if (!clipboardAvailable) {
    return (
      <button
        disabled
        title="Copy unavailable"
        className={cn(
          'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm opacity-50 cursor-not-allowed border border-border-accent bg-otel-blue-subtle text-foreground-muted',
          className,
        )}
        aria-label="Copy unavailable"
      >
        <Clipboard className="h-3.5 w-3.5" aria-hidden="true" />
        {label}
      </button>
    )
  }

  return (
    <button
      onClick={() => void handleCopy()}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm transition-colors',
        copied
          ? 'bg-green-900/60 border border-green-800 text-green-300'
          : 'bg-otel-blue-subtle border border-border-accent text-foreground-secondary hover:bg-border-accent hover:text-foreground',
        className,
      )}
      aria-label={copied ? 'Copied!' : 'Copy to clipboard'}
    >
      {copied ? (
        <Check className="h-3.5 w-3.5" aria-hidden="true" />
      ) : (
        <Clipboard className="h-3.5 w-3.5" aria-hidden="true" />
      )}
      {copied ? 'Copied!' : label}
    </button>
  )
}

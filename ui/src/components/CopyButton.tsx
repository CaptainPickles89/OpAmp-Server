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
        className={cn('inline-flex items-center gap-1.5 rounded px-2.5 py-1 text-sm opacity-50 cursor-not-allowed', className)}
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
        'inline-flex items-center gap-1.5 rounded px-2.5 py-1 text-sm transition-colors',
        copied
          ? 'bg-green-900 text-green-300'
          : 'bg-slate-700 text-slate-200 hover:bg-slate-600',
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

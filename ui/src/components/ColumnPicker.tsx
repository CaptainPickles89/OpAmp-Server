import { useEffect, useRef, useState } from 'react'
import { Columns } from 'lucide-react'

interface ColumnPickerProps {
  allKeys: string[]
  enabledKeys: string[]
  onToggle: (key: string) => void
}

export function ColumnPicker({ allKeys, enabledKeys, onToggle }: ColumnPickerProps) {
  const [isOpen, setIsOpen] = useState(false)
  const popoverRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!isOpen) return

    function handleMouseDown(event: MouseEvent) {
      if (popoverRef.current && !popoverRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleMouseDown)
    return () => {
      document.removeEventListener('mousedown', handleMouseDown)
    }
  }, [isOpen])

  useEffect(() => {
    if (!isOpen) return

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsOpen(false)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen])

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(prev => !prev)}
        aria-label="Configure visible columns"
        aria-expanded={isOpen}
        aria-controls="column-picker-popover"
        className="rounded-full border border-border-accent bg-card px-3 py-2 text-xs font-medium text-foreground-muted hover:text-foreground hover:border-otel-blue-hover transition-colors"
      >
        <Columns size={16} className="mr-2 inline-block" />
        Columns
      </button>

      {isOpen && (
        <div
          ref={popoverRef}
          id="column-picker-popover"
          role="dialog"
          aria-label="Column visibility"
          className="absolute right-0 mt-2 z-50 min-w-[200px] max-h-[320px] overflow-y-auto border border-border rounded-lg bg-card shadow-[0_4px_16px_rgba(0,0,0,0.3)] p-4"
        >
          <p className="text-xs font-medium text-foreground-subtle mb-2">Columns</p>
          <hr className="border-border mb-2" />
          {allKeys.length === 0 ? (
            <p className="text-sm text-foreground-muted">No resource attributes reported yet.</p>
          ) : (
            <ul>
              {allKeys.map(key => (
                <li key={key} className="flex items-center gap-2 py-2">
                  <input
                    type="checkbox"
                    id={key}
                    checked={enabledKeys.includes(key)}
                    onChange={() => onToggle(key)}
                    className="accent-otel-blue"
                  />
                  <label htmlFor={key} className="text-sm text-foreground cursor-pointer">
                    {key}
                  </label>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}

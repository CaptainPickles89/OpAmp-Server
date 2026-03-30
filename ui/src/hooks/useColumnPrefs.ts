import { useState } from 'react'

const STORAGE_KEY = 'opamp-column-prefs'
const DEFAULT_KEYS = ['host.name']

function readFromStorage(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw === null) return DEFAULT_KEYS
    const parsed = JSON.parse(raw) as unknown
    if (Array.isArray(parsed)) return parsed as string[]
  } catch {
    // localStorage unavailable or JSON parse failure
  }
  return DEFAULT_KEYS
}

export function useColumnPrefs() {
  const [enabledKeys, setEnabledKeys] = useState<string[]>(readFromStorage)

  function toggleKey(key: string): void {
    setEnabledKeys(prev => {
      const next = prev.includes(key)
        ? prev.filter(k => k !== key)
        : [...prev, key]
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      return next
    })
  }

  return { enabledKeys, toggleKey }
}

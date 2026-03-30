/**
 * TDD RED stubs for useColumnPrefs hook (COLS-04, COLS-06).
 * All tests fail because @/hooks/useColumnPrefs does not exist yet.
 */
import { renderHook, act } from '@testing-library/react'
import { useColumnPrefs } from '@/hooks/useColumnPrefs'

describe('useColumnPrefs', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('seeds with ["host.name"] when localStorage empty', () => {
    const { result } = renderHook(() => useColumnPrefs())
    expect(result.current.enabledKeys).toEqual(['host.name'])
  })

  it('toggleKey adds key to enabledKeys', () => {
    const { result } = renderHook(() => useColumnPrefs())
    act(() => {
      result.current.toggleKey('os.type')
    })
    expect(result.current.enabledKeys).toContain('host.name')
    expect(result.current.enabledKeys).toContain('os.type')
  })

  it('toggleKey removes existing key', () => {
    const { result } = renderHook(() => useColumnPrefs())
    act(() => {
      result.current.toggleKey('host.name')
    })
    expect(result.current.enabledKeys).toEqual([])
  })

  it('persists to localStorage on toggle', () => {
    const { result } = renderHook(() => useColumnPrefs())
    act(() => {
      result.current.toggleKey('os.type')
    })
    const stored = localStorage.getItem('opamp-column-prefs')
    expect(stored).not.toBeNull()
    const parsed = JSON.parse(stored!)
    expect(parsed).toContain('host.name')
    expect(parsed).toContain('os.type')
  })

  it('reads persisted state on mount', () => {
    localStorage.setItem('opamp-column-prefs', JSON.stringify(['os.type', 'env']))
    const { result } = renderHook(() => useColumnPrefs())
    expect(result.current.enabledKeys).toEqual(['os.type', 'env'])
  })
})

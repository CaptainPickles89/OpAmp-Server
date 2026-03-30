import '@testing-library/jest-dom'
import { server } from './mocks/server'

// Node.js 22+ exposes a built-in localStorage global that shadows jsdom's
// Storage implementation. The Node built-in lacks clear(), getItem(), etc.
// We fix this by pointing globalThis.localStorage at jsdom's internal
// _localStorage object (which is a proper Storage instance).
// This must run before any test imports useColumnPrefs or similar hooks.
if (typeof window !== 'undefined' && '_localStorage' in window) {
  const jsdomStorage = (window as unknown as Record<string, unknown>)['_localStorage']
  Object.defineProperty(globalThis, 'localStorage', {
    value: jsdomStorage,
    configurable: true,
    writable: true,
  })
}

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

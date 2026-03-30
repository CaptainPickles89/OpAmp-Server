import { describe, it, expect } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '@/mocks/server'
import { renderWithProviders } from '@/test/renderWithProviders'
import { StatusPage } from '../StatusPage'

describe('StatusPage', () => {
  it('renders hero heading "OpAMP Server" (STATUS-01)', async () => {
    renderWithProviders(<StatusPage />)
    expect(screen.getByRole('heading', { level: 1, name: /OpAMP Server/i })).toBeTruthy()
  })

  it('renders description text (STATUS-02)', async () => {
    renderWithProviders(<StatusPage />)
    expect(
      screen.getByText(/management interface for OpenTelemetry Collector fleets/i),
    ).toBeTruthy()
  })

  it('renders agent health count from API (STATUS-03)', async () => {
    renderWithProviders(<StatusPage />)
    await waitFor(() => {
      expect(screen.getByText(/1 of 2/)).toBeTruthy()
    })
  })

  it('renders loading skeleton before data arrives (STATUS-01)', () => {
    server.use(
      http.get('/api/v1/stats', async () => {
        await new Promise(r => setTimeout(r, 200))
        return HttpResponse.json({ healthy_count: 1, total_count: 2 })
      }),
    )

    renderWithProviders(<StatusPage />)
    const skeleton = document.querySelector('[aria-label="Loading agent stats"]')
    expect(skeleton).toBeTruthy()
  })

  it('shows empty state message when 0 collectors (STATUS-03)', async () => {
    server.use(
      http.get('/api/v1/stats', () =>
        HttpResponse.json({ healthy_count: 0, total_count: 0 }),
      ),
    )

    renderWithProviders(<StatusPage />)
    await waitFor(() => {
      expect(screen.getByText(/No collectors connected/i)).toBeTruthy()
    })
  })
})

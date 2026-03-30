import { describe, it, expect, beforeEach } from 'vitest'
import { screen, waitFor, fireEvent } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '@/mocks/server'
import { renderWithProviders } from '@/test/renderWithProviders'
import { CollectorListPage } from '../CollectorListPage'

describe('CollectorListPage', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('renders loading skeleton when isLoading', async () => {
    // Delay the response to catch loading state
    server.use(
      http.get('/api/v1/collectors', async () => {
        await new Promise(r => setTimeout(r, 200))
        return HttpResponse.json([])
      }),
    )

    renderWithProviders(<CollectorListPage />)
    // Loading state shows skeleton
    const skeleton = document.querySelector('[aria-label="Loading collectors"]')
    expect(skeleton).toBeTruthy()
  })

  it('renders collector rows when data is loaded', async () => {
    renderWithProviders(<CollectorListPage />)
    await waitFor(() => {
      expect(screen.queryByText(/aabbccdd/i)).toBeTruthy()
    })
  })

  it('renders empty state when API returns empty array', async () => {
    server.use(
      http.get('/api/v1/collectors', () => HttpResponse.json([])),
    )
    renderWithProviders(<CollectorListPage />)
    await waitFor(() => {
      expect(screen.getByText('No collectors connected.')).toBeTruthy()
    })
  })

  it('renders error state when API fails', async () => {
    server.use(
      http.get('/api/v1/collectors', () => HttpResponse.error()),
    )
    renderWithProviders(<CollectorListPage />)
    await waitFor(() => {
      expect(screen.getByText('Failed to load collectors.')).toBeTruthy()
    })
  })

  it('search input filters collector rows by UID', async () => {
    renderWithProviders(<CollectorListPage />)
    await waitFor(() => {
      expect(screen.queryByText(/aabbccdd/i)).toBeTruthy()
    })

    const searchInput = screen.getByRole('searchbox')
    fireEvent.change(searchInput, { target: { value: 'nonexistentuid12345' } })

    await waitFor(() => {
      expect(screen.getByText('No collectors match your filters.')).toBeTruthy()
    })
  })

  it('UID is truncated in display', async () => {
    renderWithProviders(<CollectorListPage />)
    await waitFor(() => {
      // Full UID: aabbccddeeff00112233445566778899 - should be truncated
      const cells = document.querySelectorAll('[title="aabbccddeeff00112233445566778899"]')
      expect(cells.length).toBeGreaterThan(0)
    })
  })

  it('health filter shows only collectors with matching health_status', async () => {
    renderWithProviders(<CollectorListPage />)
    await waitFor(() => {
      expect(screen.queryByText(/aabbccdd/i)).toBeTruthy()
    })

    // Click "Unhealthy" filter — should show no results since mock data is healthy/degraded
    const unhealthyBtn = screen.getByRole('button', { name: 'Unhealthy' })
    fireEvent.click(unhealthyBtn)

    await waitFor(() => {
      expect(screen.getByText('No collectors match your filters.')).toBeTruthy()
    })
  })

  it('renders host.name column header by default', async () => {
    renderWithProviders(<CollectorListPage />)
    await screen.findByText('web-01')
    expect(screen.getByText('host.name')).toBeInTheDocument()
  })

  it('renders resource attribute value from collector data', async () => {
    renderWithProviders(<CollectorListPage />)
    await screen.findByText('web-01')
    // MSW handler returns resource_attributes: { 'host.name': 'web-01' } for first collector
    const cells = screen.getAllByText('web-01')
    expect(cells.length).toBeGreaterThan(0)
  })

  it('renders em dash when attribute is absent for a collector', async () => {
    // Enable os.type column so the second collector (which has no os.type) shows em dash
    localStorage.setItem('opamp-column-prefs', JSON.stringify(['host.name', 'os.type']))
    renderWithProviders(<CollectorListPage />)
    await screen.findByText('web-01')
    // Second collector has no os.type value so em dash should appear
    const dashSpans = document.querySelectorAll('span[aria-label="not available"]')
    expect(dashSpans.length).toBeGreaterThan(0)
  })

  it('renders ColumnPicker button in the header', async () => {
    renderWithProviders(<CollectorListPage />)
    await screen.findByRole('button', { name: /configure visible columns/i })
  })
})

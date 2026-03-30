import { screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { renderWithProviders } from '@/test/renderWithProviders'
import { GettingStartedPage } from '../GettingStartedPage'

describe('GettingStartedPage', () => {
  it('renders "Getting Started" heading', () => {
    renderWithProviders(<GettingStartedPage />)
    expect(screen.getByText('Getting Started')).toBeTruthy()
  })

  it('renders 3-step instructions', () => {
    renderWithProviders(<GettingStartedPage />)
    const steps = document.querySelectorAll('li')
    expect(steps.length).toBeGreaterThanOrEqual(3)
  })

  it('renders the base config YAML code editor', () => {
    renderWithProviders(<GettingStartedPage />)
    const editors = screen.getAllByTestId('config-editor')
    expect(editors.length).toBeGreaterThan(0)
  })

  it('renders Copy Config button', () => {
    // Mock clipboard API
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: vi.fn().mockResolvedValue(undefined) },
      writable: true,
      configurable: true,
    })
    renderWithProviders(<GettingStartedPage />)
    expect(screen.getByText('Copy Config')).toBeTruthy()
  })

  it('renders server endpoint URL with /v1/opamp path', () => {
    renderWithProviders(<GettingStartedPage />)
    const endpointEl = document.querySelector('code.font-mono.text-otel-amber')
    expect(endpointEl?.textContent).toContain('/v1/opamp')
  })

  it('server endpoint URL uses window.location.origin', () => {
    renderWithProviders(<GettingStartedPage />)
    const endpointEl = document.querySelector('code.font-mono.text-otel-amber')
    expect(endpointEl?.textContent).toContain(window.location.origin)
  })

  it('BASE_CONFIG_YAML includes host.name resource attribute', () => {
    const { container } = renderWithProviders(<GettingStartedPage />)
    expect(container.textContent).toContain('host.name')
  })

  it('BASE_CONFIG_YAML includes service.instance.id resource attribute', () => {
    const { container } = renderWithProviders(<GettingStartedPage />)
    expect(container.textContent).toContain('service.instance.id')
  })

  it('BASE_CONFIG_YAML includes deployment.environment resource attribute', () => {
    const { container } = renderWithProviders(<GettingStartedPage />)
    expect(container.textContent).toContain('deployment.environment')
  })

  it('BASE_CONFIG_YAML includes host.ip resource attribute', () => {
    const { container } = renderWithProviders(<GettingStartedPage />)
    expect(container.textContent).toContain('host.ip')
  })
})

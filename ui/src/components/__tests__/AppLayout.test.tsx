import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AppLayout } from '../AppLayout'

function renderAppLayout(initialEntries: string[] = ['/']) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <AppLayout>
        <div>content</div>
      </AppLayout>
    </MemoryRouter>,
  )
}

describe('AppLayout', () => {
  it('renders Status nav link (STATUS-04)', () => {
    renderAppLayout()
    const statusLink = screen.getByRole('link', { name: 'Status' })
    expect(statusLink).toBeTruthy()
    expect(statusLink.getAttribute('href')).toBe('/')
  })

  it('Status link is first nav item', () => {
    renderAppLayout()
    const navLinks = screen.getAllByRole('link')
    // First link is brand link (to="/"), second is the first nav pill item
    // Find all nav pill links by their text
    const statusLink = screen.getByRole('link', { name: 'Status' })
    const collectorsLink = screen.getByRole('link', { name: 'Collectors' })
    const allLinks = Array.from(document.querySelectorAll('nav a'))
    const statusIndex = allLinks.indexOf(statusLink)
    const collectorsIndex = allLinks.indexOf(collectorsLink)
    expect(statusIndex).toBeLessThan(collectorsIndex)
  })

  it('Status link is active on root path', () => {
    renderAppLayout(['/'])
    const statusLink = screen.getByRole('link', { name: 'Status' })
    expect(statusLink.className).toContain('bg-otel-blue')
  })

  it('Status link is not active on /collectors', () => {
    renderAppLayout(['/collectors'])
    const statusLink = screen.getByRole('link', { name: 'Status' })
    expect(statusLink.className).not.toContain('bg-otel-blue')
  })
})

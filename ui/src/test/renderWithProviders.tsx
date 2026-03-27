import type { ReactNode } from 'react'
import { render } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

interface RenderOptions {
  initialEntries?: string[]
  // Provide a route pattern to enable useParams (e.g. '/collectors/:id')
  routePattern?: string
}

export function renderWithProviders(
  ui: ReactNode,
  { initialEntries = ['/'], routePattern }: RenderOptions = {},
) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
        gcTime: 0,
      },
    },
  })

  const content = routePattern ? (
    <Routes>
      <Route path={routePattern} element={ui} />
    </Routes>
  ) : ui

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        {content}
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

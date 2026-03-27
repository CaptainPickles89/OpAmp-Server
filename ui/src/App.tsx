import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { CollectorListPage } from '@/pages/CollectorListPage'
import { CollectorDetailPage } from '@/pages/CollectorDetailPage'
import { GettingStartedPage } from '@/pages/GettingStartedPage'
import { AppLayout } from '@/components/AppLayout'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 4000,
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
})

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppLayout>
          <Routes>
            <Route path="/" element={<Navigate to="/collectors" replace />} />
            <Route path="/collectors" element={<CollectorListPage />} />
            <Route path="/collectors/:id" element={<CollectorDetailPage />} />
            <Route path="/getting-started" element={<GettingStartedPage />} />
          </Routes>
        </AppLayout>
      </BrowserRouter>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}

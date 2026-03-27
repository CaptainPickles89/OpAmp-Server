import { useQuery } from '@tanstack/react-query'
import { fetchCollectors } from '@/api/client'

export function useCollectors() {
  return useQuery({
    queryKey: ['collectors'],
    queryFn: fetchCollectors,
    refetchInterval: 5000,
    staleTime: 4000,
  })
}

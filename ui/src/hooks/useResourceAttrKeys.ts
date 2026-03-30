import { useQuery } from '@tanstack/react-query'
import { fetchResourceAttrKeys } from '@/api/client'

export function useResourceAttrKeys() {
  return useQuery({
    queryKey: ['resource-attr-keys'],
    queryFn: fetchResourceAttrKeys,
    refetchInterval: 5000,
    staleTime: 4000,
  })
}

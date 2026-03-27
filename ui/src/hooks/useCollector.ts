import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchCollector, pushConfig, ApiError } from '@/api/client'

export function useCollector(id: string) {
  const [isActivePush, setIsActivePush] = useState(false)

  const query = useQuery({
    queryKey: ['collector', id],
    queryFn: () => fetchCollector(id),
    refetchInterval: isActivePush ? 2000 : 5000,
    enabled: !!id,
    retry: (failureCount, error) => {
      // Don't retry on 404
      if (error instanceof ApiError && error.status === 404) return false
      return failureCount < 2
    },
  })

  useEffect(() => {
    const state = query.data?.push_status.push_state
    setIsActivePush(state === 'PUSH_PENDING' || state === 'APPLYING')
  }, [query.data?.push_status.push_state])

  return query
}

export function usePushConfig(id: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (yamlContent: string) => pushConfig(id, yamlContent),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['collector', id] })
    },
  })
}

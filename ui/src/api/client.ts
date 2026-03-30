import type { CollectorSummary, CollectorDetail, Stats } from './types'
import { CollectorSummarySchema, CollectorDetailSchema, PushStatusSchema, StatsSchema, ResourceAttrKeysSchema } from './types'
import type { PushStatus } from './types'

class ApiError extends Error {
  status: number

  constructor(
    status: number,
    message: string,
  ) {
    super(message)
    this.status = status
    this.name = 'ApiError'
  }
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options)
  if (!response.ok) {
    throw new ApiError(response.status, `API error ${response.status}: ${response.statusText}`)
  }
  return response.json() as Promise<T>
}

export async function fetchCollectors(): Promise<CollectorSummary[]> {
  const data = await request<unknown[]>('/api/v1/collectors')
  return data.map(item => CollectorSummarySchema.parse(item))
}

export async function fetchCollector(id: string): Promise<CollectorDetail> {
  const data = await request<unknown>(`/api/v1/collectors/${id}`)
  return CollectorDetailSchema.parse(data)
}

export async function pushConfig(id: string, yaml: string): Promise<PushStatus> {
  const data = await request<unknown>(`/api/v1/collectors/${id}/config`, {
    method: 'POST',
    headers: { 'Content-Type': 'text/plain' },
    body: yaml,
  })
  return PushStatusSchema.parse(data)
}

export async function fetchStats(): Promise<Stats> {
  const data = await request<unknown>('/api/v1/stats')
  return StatsSchema.parse(data)
}

export async function fetchResourceAttrKeys(): Promise<string[]> {
  const data = await request<unknown>('/api/v1/collectors/attrs/keys')
  return ResourceAttrKeysSchema.parse(data).keys
}

export { ApiError }

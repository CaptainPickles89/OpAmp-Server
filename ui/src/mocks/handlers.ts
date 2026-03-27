import { http, HttpResponse } from 'msw'
import type { CollectorSummary, CollectorDetail } from '@/api/types'

const mockCollectors: CollectorSummary[] = [
  {
    instance_uid: 'aabbccddeeff00112233445566778899',
    last_seen: Date.now() * 1_000_000,
    health_status: 'healthy',
    capabilities: 19463,
  },
  {
    instance_uid: 'bbccddeeff001122334455667788990a',
    last_seen: (Date.now() - 60000) * 1_000_000,
    health_status: 'degraded',
    capabilities: 19463,
  },
]

const mockCollectorDetail: CollectorDetail = {
  instance_uid: 'aabbccddeeff00112233445566778899',
  first_seen: (Date.now() - 3600000) * 1_000_000,
  last_seen: Date.now() * 1_000_000,
  health_status: 'healthy',
  capabilities: 19463,
  health_history: [
    {
      recorded_at: Date.now() * 1_000_000,
      healthy: true,
      status: 'ok',
      last_error: null,
    },
  ],
  effective_config: {
    recorded_at: (Date.now() - 1800000) * 1_000_000,
    config_hash: 'abc123',
    config_json: {
      'collector.yaml': {
        body: 'receivers:\n  otlp:\n    protocols:\n      grpc:\n\nservice:\n  pipelines:\n    traces:\n      receivers: [otlp]\n',
        content_type: 'text/yaml',
      },
    },
  },
  push_status: {
    push_state: 'IDLE',
    pending_config_hash: null,
  },
}

export const handlers = [
  http.get('/api/v1/collectors', () => {
    return HttpResponse.json(mockCollectors)
  }),

  http.get('/api/v1/collectors/:id', ({ params }) => {
    const { id } = params
    if (id === 'notfound') {
      return new HttpResponse(null, { status: 404 })
    }
    return HttpResponse.json({
      ...mockCollectorDetail,
      instance_uid: String(id),
    })
  }),

  http.post('/api/v1/collectors/:id/config', () => {
    return HttpResponse.json(
      { push_state: 'PUSH_PENDING', pending_config_hash: null },
      { status: 202 },
    )
  }),
]
